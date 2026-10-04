from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.agents.duplicate_agent import DuplicateDetectionAgent
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.incident_history import IncidentHistory
from app.orchestrator.orchestrator import Orchestrator


def save_candidates(
    incident_id: int,
    candidates: list[dict[str, Any]],
    db: Session,
) -> dict[str, int]:
    """Save suggested pairs as 'pending'. Human decisions are never changed."""

    stats = {"new": 0, "updated": 0, "kept_human_decision": 0}

    for candidate in candidates:
        other_id = candidate["candidate_incident_id"]

        factors = {
            key: candidate[key]
            for key in (
                "strength",
                "same_emergency_type",
                "distance_km",
                "hours_apart",
                "warnings",
            )
        }

        existing = (
            db.query(DuplicateCandidate)
            .filter(
                or_(
                    and_(
                        DuplicateCandidate.incident_id == incident_id,
                        DuplicateCandidate.candidate_incident_id == other_id,
                    ),
                    and_(
                        DuplicateCandidate.incident_id == other_id,
                        DuplicateCandidate.candidate_incident_id == incident_id,
                    ),
                )
            )
            .first()
        )

        if existing is None:
            db.add(
                DuplicateCandidate(
                    incident_id=incident_id,
                    candidate_incident_id=other_id,
                    similarity=candidate["similarity"],
                    factors=factors,
                    status="pending",
                )
            )
            stats["new"] += 1
        elif existing.status == "pending":
            existing.similarity = candidate["similarity"]
            existing.factors = factors
            stats["updated"] += 1
        else:
            stats["kept_human_decision"] += 1

    db.commit()
    return stats


def check_for_duplicates(incident_id: int, db: Session) -> dict[str, Any]:
    """Run the Duplicate Detection Agent and save its suggestions."""

    orchestrator = Orchestrator(
        [DuplicateDetectionAgent(db)],
        max_retries=1,
    )

    pipeline = orchestrator.run(
        {"incident_id": incident_id},
        db,
        incident_id=incident_id,
    )

    if pipeline.status != "completed":
        failed_step = pipeline.steps[-1] if pipeline.steps else None
        error = failed_step.error if failed_step else "unknown error"

        db.add(
            IncidentHistory(
                incident_id=incident_id,
                action="duplicate_check_failed",
                notes=f"Duplicate check failed: {error}",
            )
        )
        db.commit()

        return {
            "status": "failed",
            "error": error,
            "potential_duplicates": 0,
            "candidates": [],
        }

    result = pipeline.results["duplicate_agent"]
    output = result["output"]
    candidates = output["candidates"]

    saved = save_candidates(incident_id, candidates, db)

    if candidates:
        db.add(
            IncidentHistory(
                incident_id=incident_id,
                action="duplicates_flagged",
                notes=(
                    f"{len(candidates)} potential duplicate(s) flagged for "
                    "human review. Nothing was merged."
                ),
            )
        )
        db.commit()

    return {
        "status": "completed",
        "potential_duplicates": len(candidates),
        "candidates": candidates,
        "compared_with": output["compared_with"],
        "excluded_due_to_distance": output["excluded_due_to_distance"],
        "threshold": output["threshold"],
        "saved": saved,
        "explanation": result["explanation"],
        "requires_human_confirmation": True,
    }