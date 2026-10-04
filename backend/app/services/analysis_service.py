from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.agents.intake_agent import IntakeAgent
from app.agents.location_agent import LocationAgent
from app.agents.severity_agent import SeverityAgent
from app.models.emergency_report import EmergencyReport
from app.models.incident import Incident
from app.models.incident_history import IncidentHistory
from app.models.incident_location import IncidentLocation
from app.orchestrator.orchestrator import Orchestrator
from app.schemas.agent import PipelineResult
from app.schemas.analysis import ReportAnalysisResponse
from app.services.duplicate_service import check_for_duplicates


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _label(emergency_type: str) -> str:
    return emergency_type.replace("_", " ").title()


def build_report_input(report: EmergencyReport) -> dict[str, Any]:
    """Convert a database report into the input the agents expect."""

    return {
        "report_id": report.id,
        "description": report.description,
        "selected_emergency_type": report.emergency_type,
        "address": report.address,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "reported_at": report.created_at.isoformat(),
    }


def _agent_output(pipeline: PipelineResult, agent_name: str) -> dict[str, Any]:
    return (pipeline.results.get(agent_name) or {}).get("output") or {}


def build_summary(pipeline: PipelineResult) -> dict[str, Any]:
    """Small overview for dashboards. Full details stay in the pipeline."""

    intake = _agent_output(pipeline, "intake_agent")
    location = _agent_output(pipeline, "location_agent")
    severity = _agent_output(pipeline, "severity_agent")

    missing: list[str] = []
    seen: set[str] = set()

    for data in pipeline.results.values():
        for item in data.get("missing_information") or []:
            key = item.strip().lower()

            if key and key not in seen:
                seen.add(key)
                missing.append(item)

    return {
        "emergency_type": intake.get("emergency_type"),
        "type_mismatch": intake.get("type_mismatch"),
        "severity": severity.get("severity"),
        "severity_score": severity.get("score"),
        "urgency_rank": severity.get("urgency_rank"),
        "location_certainty": location.get("location_certainty"),
        "map_ready": location.get("map_ready"),
        "needs_location_verification": location.get(
            "needs_location_verification"
        ),
        "missing_information": missing,
    }


def _get_or_create_incident(
    report: EmergencyReport,
    db: Session,
) -> tuple[Incident, bool]:
    """Return the report's incident, creating it if the report has none."""

    if report.incident_id is not None:
        existing = (
            db.query(Incident)
            .filter(Incident.id == report.incident_id)
            .first()
        )

        if existing is not None:
            return existing, False

    incident = Incident(
        incident_code=f"TMP-{uuid4().hex}",
        title=f"{_label(report.emergency_type)} report"[:255],
        description=report.description,
        emergency_type=report.emergency_type,
        severity="unknown",
        status="pending",
        report_count=1,
    )
    db.add(incident)
    db.flush()

    incident.incident_code = f"INC-{incident.id:05d}"
    report.incident_id = incident.id

    db.add(
        IncidentHistory(
            incident_id=incident.id,
            action="incident_created",
            new_value=incident.incident_code,
            notes=f"Created from emergency report #{report.id}",
        )
    )
    db.commit()
    db.refresh(incident)

    return incident, True


def _save_analysis(
    report: EmergencyReport,
    incident: Incident,
    pipeline: PipelineResult,
    summary: dict[str, Any],
    is_new: bool,
    db: Session,
) -> None:
    """Store the pipeline result on the incident and write the history."""

    if pipeline.status != "completed":
        failed_step = pipeline.steps[-1] if pipeline.steps else None
        error = failed_step.error if failed_step else "unknown error"

        db.add(
            IncidentHistory(
                incident_id=incident.id,
                action="ai_analysis_failed",
                notes=(
                    f"Pipeline stopped at {pipeline.failed_agent}: {error}. "
                    "The report needs manual review."
                ),
            )
        )
        db.commit()
        return

    location = _agent_output(pipeline, "location_agent")
    severity_output = _agent_output(pipeline, "severity_agent")

    old_severity = incident.severity
    new_severity = summary.get("severity") or "unknown"

    label = _label(report.emergency_type)
    location_text = location.get("location_summary")
    has_location = location.get("location_certainty") not in (None, "none")

    if has_location and location_text:
        title = f"{label} - {location_text}"
    else:
        title = f"{label} incident"

    incident.title = title[:255]
    incident.severity = new_severity
    incident.ai_analysis = jsonable_encoder(
        {
            "analyzed_at": _utc_now().isoformat(),
            "pipeline_status": pipeline.status,
            "summary": summary,
            "results": pipeline.results,
            "requires_human_verification": True,
        }
    )

    coordinates = location.get("coordinates")

    if coordinates:
        has_row = (
            db.query(IncidentLocation.id)
            .filter(IncidentLocation.incident_id == incident.id)
            .first()
        )

        if has_row is None:
            db.add(
                IncidentLocation(
                    incident_id=incident.id,
                    latitude=coordinates["latitude"],
                    longitude=coordinates["longitude"],
                    address=location.get("normalized_address"),
                    location_source="report",
                )
            )

    prefix = "Initial AI estimate" if is_new else "AI re-analysis"
    rules_version = severity_output.get("rules_version", "unknown")

    db.add(
        IncidentHistory(
            incident_id=incident.id,
            action="ai_severity_assessed",
            old_value=old_severity,
            new_value=new_severity,
            notes=(
                f"{prefix} (severity rules {rules_version}); "
                "not verified, requires human review"
            ),
        )
    )
    db.commit()


def analyze_report(
    report: EmergencyReport,
    db: Session,
) -> ReportAnalysisResponse:
    """Create/find the incident, run the agents, and save the result."""

    incident, is_new = _get_or_create_incident(report, db)
    incident_id = incident.id
    incident_code = incident.incident_code

    orchestrator = Orchestrator(
        [IntakeAgent(), LocationAgent(), SeverityAgent()],
        max_retries=2,
    )

    pipeline = orchestrator.run(
        build_report_input(report),
        db,
        incident_id=incident_id,
    )
    summary = build_summary(pipeline)

    _save_analysis(report, incident, pipeline, summary, is_new, db)

    if pipeline.status == "completed":
        duplicate_check = check_for_duplicates(incident_id, db)
    else:
        duplicate_check = {
            "status": "skipped",
            "reason": "AI analysis did not complete",
        }

    return ReportAnalysisResponse(
        report_id=report.id,
        incident_id=incident_id,
        incident_code=incident_code,
        status=pipeline.status,
        summary=summary,
        pipeline=pipeline,
        duplicate_check=duplicate_check,
    )