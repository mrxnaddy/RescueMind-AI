from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.agents.severity_agent import URGENCY_RANK
from app.models.audit_log import AuditLog
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.emergency_report import EmergencyReport
from app.models.incident import Incident
from app.models.incident_history import IncidentHistory
from app.models.incident_location import IncidentLocation
from app.schemas.duplicate import (
    DuplicateCandidateView,
    DuplicateIncidentView,
    ReportBrief,
)


class ReviewError(Exception):
    """A review action could not be done (carries an HTTP status code)."""

    def __init__(self, message: str, status_code: int = 409) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _incident_view(
    incident: Incident,
    reports: list[EmergencyReport],
) -> DuplicateIncidentView:
    return DuplicateIncidentView(
        id=incident.id,
        incident_code=incident.incident_code,
        title=incident.title,
        emergency_type=incident.emergency_type,
        severity=incident.severity,
        status=incident.status,
        report_count=incident.report_count,
        created_at=incident.created_at,
        reports=[ReportBrief.model_validate(report) for report in reports],
    )


def build_candidate_views(
    candidates: list[DuplicateCandidate],
    db: Session,
) -> list[DuplicateCandidateView]:
    """Candidates with both incidents and their original reports."""

    ids = {item.incident_id for item in candidates} | {
        item.candidate_incident_id for item in candidates
    }

    if not ids:
        return []

    incidents = {
        incident.id: incident
        for incident in db.query(Incident).filter(Incident.id.in_(ids)).all()
    }

    reports_by_incident: dict[int, list[EmergencyReport]] = {}

    for report in (
        db.query(EmergencyReport)
        .filter(EmergencyReport.incident_id.in_(ids))
        .order_by(EmergencyReport.id)
        .all()
    ):
        reports_by_incident.setdefault(report.incident_id, []).append(report)

    views: list[DuplicateCandidateView] = []

    for item in candidates:
        views.append(
            DuplicateCandidateView(
                id=item.id,
                similarity=item.similarity,
                strength=(item.factors or {}).get("strength"),
                status=item.status,
                factors=item.factors,
                review_notes=item.review_notes,
                reviewed_at=item.reviewed_at,
                created_at=item.created_at,
                incident=_incident_view(
                    incidents[item.incident_id],
                    reports_by_incident.get(item.incident_id, []),
                ),
                candidate=_incident_view(
                    incidents[item.candidate_incident_id],
                    reports_by_incident.get(item.candidate_incident_id, []),
                ),
            )
        )

    return views


def _get_pending_candidate(candidate_id: int, db: Session) -> DuplicateCandidate:
    candidate = (
        db.query(DuplicateCandidate)
        .filter(DuplicateCandidate.id == candidate_id)
        .first()
    )

    if candidate is None:
        raise ReviewError("Duplicate candidate not found", 404)

    if candidate.status != "pending":
        raise ReviewError(
            f"This candidate was already reviewed (status: {candidate.status})",
            409,
        )

    return candidate


def confirm_merge(
    candidate_id: int,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    """A human confirmed the duplicate: merge the newer incident into the older.

    Original reports are never deleted; they are re-pointed to the primary.
    """

    candidate = _get_pending_candidate(candidate_id, db)

    first = db.query(Incident).filter(Incident.id == candidate.incident_id).first()
    second = (
        db.query(Incident)
        .filter(Incident.id == candidate.candidate_incident_id)
        .first()
    )

    if first is None or second is None:
        raise ReviewError("One of the incidents no longer exists", 404)

    if "merged" in (first.status, second.status):
        raise ReviewError(
            "One of these incidents was already merged into another incident",
            409,
        )

    if first.created_at <= second.created_at:
        primary, secondary = first, second
    else:
        primary, secondary = second, first

    now = _utc_now()

    # 1. Move the original reports to the primary incident.
    moved_reports = (
        db.query(EmergencyReport)
        .filter(EmergencyReport.incident_id == secondary.id)
        .all()
    )
    moved_ids = [report.id for report in moved_reports]

    for report in moved_reports:
        report.incident_id = primary.id

    db.flush()

    primary.report_count = (
        db.query(func.count(EmergencyReport.id))
        .filter(EmergencyReport.incident_id == primary.id)
        .scalar()
    )

    # 2. Never lower the urgency: keep the higher AI severity estimate.
    old_severity = primary.severity
    severity_raised = URGENCY_RANK.get(secondary.severity, 0) > URGENCY_RANK.get(
        primary.severity, 0
    )

    if severity_raised:
        primary.severity = secondary.severity

    # 3. If the primary has no map location, take the other incident's.
    primary_has_location = (
        db.query(IncidentLocation.id)
        .filter(IncidentLocation.incident_id == primary.id)
        .first()
        is not None
    )
    moved_locations = 0

    if not primary_has_location:
        for location in (
            db.query(IncidentLocation)
            .filter(IncidentLocation.incident_id == secondary.id)
            .all()
        ):
            location.incident_id = primary.id
            moved_locations += 1

    # 4. Mark the secondary as merged.
    secondary.status = "merged"

    # 5. Other pending suggestions about the merged incident are now stale.
    stale = (
        db.query(DuplicateCandidate)
        .filter(
            DuplicateCandidate.id != candidate.id,
            DuplicateCandidate.status == "pending",
            or_(
                DuplicateCandidate.incident_id == secondary.id,
                DuplicateCandidate.candidate_incident_id == secondary.id,
            ),
        )
        .all()
    )

    for item in stale:
        item.status = "superseded"
        item.reviewed_at = now
        item.review_notes = (
            f"Incident {secondary.incident_code} was merged into "
            f"{primary.incident_code}"
        )

    candidate.status = "confirmed"
    candidate.reviewed_at = now
    candidate.review_notes = notes

    # 6. History and audit trail.
    db.add(
        IncidentHistory(
            incident_id=primary.id,
            action="merged_from",
            new_value=secondary.incident_code,
            notes=(
                f"{secondary.incident_code} was merged into this incident "
                f"after human confirmation. Reports moved: {moved_ids}."
            ),
        )
    )
    db.add(
        IncidentHistory(
            incident_id=secondary.id,
            action="merged_into",
            new_value=primary.incident_code,
            notes=(
                f"Merged into {primary.incident_code} after human "
                "confirmation. Original reports are preserved."
            ),
        )
    )

    if severity_raised:
        db.add(
            IncidentHistory(
                incident_id=primary.id,
                action="severity_raised_on_merge",
                old_value=old_severity,
                new_value=primary.severity,
                notes=(
                    "Higher AI severity estimate taken from the merged "
                    "incident; requires human review."
                ),
            )
        )

    db.add(
        AuditLog(
            user_id=None,
            action="duplicate_merge_confirmed",
            entity_type="incident",
            entity_id=primary.id,
            description=(
                f"Human confirmed merge of {secondary.incident_code} into "
                f"{primary.incident_code}"
            ),
            metadata_json=jsonable_encoder(
                {
                    "candidate_id": candidate.id,
                    "merged_incident_id": secondary.id,
                    "moved_report_ids": moved_ids,
                    "moved_locations": moved_locations,
                    "similarity": candidate.similarity,
                    "notes": notes,
                }
            ),
        )
    )

    db.commit()

    return {
        "status": "merged",
        "primary_incident": {
            "id": primary.id,
            "incident_code": primary.incident_code,
        },
        "merged_incident": {
            "id": secondary.id,
            "incident_code": secondary.incident_code,
        },
        "moved_report_ids": moved_ids,
        "report_count": primary.report_count,
        "severity": primary.severity,
        "severity_raised": severity_raised,
        "moved_locations": moved_locations,
        "superseded_candidates": len(stale),
        "note": (
            "Original reports were preserved; they now belong to the "
            "primary incident."
        ),
    }


def reject_candidate(
    candidate_id: int,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    """A human decided the two incidents are different."""

    candidate = _get_pending_candidate(candidate_id, db)

    candidate.status = "rejected"
    candidate.reviewed_at = _utc_now()
    candidate.review_notes = notes

    for incident_id in (candidate.incident_id, candidate.candidate_incident_id):
        db.add(
            IncidentHistory(
                incident_id=incident_id,
                action="duplicate_rejected",
                notes=(
                    "A human reviewed a possible duplicate (similarity "
                    f"{candidate.similarity}) and decided these are "
                    "different incidents."
                ),
            )
        )

    db.add(
        AuditLog(
            user_id=None,
            action="duplicate_rejected",
            entity_type="incident",
            entity_id=candidate.incident_id,
            description=(
                "Human rejected a possible duplicate between incidents "
                f"{candidate.incident_id} and {candidate.candidate_incident_id}"
            ),
            metadata_json=jsonable_encoder(
                {
                    "candidate_id": candidate.id,
                    "similarity": candidate.similarity,
                    "notes": notes,
                }
            ),
        )
    )

    db.commit()

    return {
        "status": "rejected",
        "candidate_id": candidate.id,
        "note": "These incidents will not be suggested as duplicates again.",
    }