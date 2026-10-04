from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.incident import Incident
from app.models.incident_history import IncidentHistory
from app.models.response_plan import ResponsePlan
from app.services.approval_service import release_incident_assignments

# Which status can follow which. "assigned" is NOT here as a manual target:
# it is only set when a human approves a response plan.
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["under_review", "resolved"],
    "under_review": ["pending", "approved", "resolved"],
    "approved": ["under_review", "in_progress", "resolved"],
    "assigned": ["in_progress", "resolved"],
    "in_progress": ["resolved"],
    "resolved": ["under_review"],
    "merged": [],
}

STATUS_MEANING: dict[str, str] = {
    "pending": "Received. Nobody has reviewed it yet.",
    "under_review": "A coordinator is reviewing the incident.",
    "approved": "The incident was approved for response.",
    "assigned": "Resources are assigned (set by approving a response plan).",
    "in_progress": "The response is under way.",
    "resolved": "The incident is closed. Assigned resources were released.",
    "merged": "Merged into another incident (set by confirming a duplicate).",
}


class StatusError(Exception):
    """A status change was refused (carries an HTTP status code)."""

    def __init__(self, message: str, status_code: int = 409) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def change_status(
    incident_id: int,
    new_status: str,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        raise StatusError("Incident not found", 404)

    old_status = incident.status

    if old_status == "merged":
        raise StatusError(
            "A merged incident cannot change status; work on the incident "
            "it was merged into",
            409,
        )

    if new_status == old_status:
        raise StatusError(f"The incident is already {old_status}", 409)

    allowed = ALLOWED_TRANSITIONS.get(old_status, ALLOWED_TRANSITIONS["pending"])

    if new_status not in allowed:
        message = (
            f"Cannot change status from '{old_status}' to '{new_status}'. "
            f"Allowed next statuses: {', '.join(allowed)}."
        )

        if new_status == "assigned":
            message += " Resources are assigned by approving a response plan."

        raise StatusError(message, 409)

    released_count = 0
    superseded_plans = 0
    superseded_reviews = 0

    if new_status == "resolved":
        released = release_incident_assignments(incident_id, notes, db)
        released_count = released["released_count"]

        # Releasing may already have moved the status (assigned -> approved).
        db.refresh(incident)
        old_status = incident.status

        now = _utc_now()

        superseded_plans = (
            db.query(ResponsePlan)
            .filter(
                ResponsePlan.incident_id == incident_id,
                ResponsePlan.status == "proposed",
            )
            .update({"status": "superseded"}, synchronize_session=False)
        )

        reviews = (
            db.query(DuplicateCandidate)
            .filter(
                DuplicateCandidate.status == "pending",
                or_(
                    DuplicateCandidate.incident_id == incident_id,
                    DuplicateCandidate.candidate_incident_id == incident_id,
                ),
            )
            .all()
        )

        for review in reviews:
            review.status = "superseded"
            review.reviewed_at = now
            review.review_notes = "Incident was resolved"

        superseded_reviews = len(reviews)

    incident.status = new_status

    db.add(
        IncidentHistory(
            incident_id=incident.id,
            action="status_changed",
            old_value=old_status,
            new_value=new_status,
            notes=notes or "Status changed by a human",
        )
    )
    db.add(
        AuditLog(
            user_id=None,
            action="incident_status_changed",
            entity_type="incident",
            entity_id=incident.id,
            description=(
                f"{incident.incident_code}: {old_status} -> {new_status}"
            ),
            metadata_json=jsonable_encoder(
                {
                    "old_status": old_status,
                    "new_status": new_status,
                    "notes": notes,
                    "released_assignments": released_count,
                    "superseded_plans": superseded_plans,
                    "superseded_duplicate_reviews": superseded_reviews,
                }
            ),
        )
    )
    db.commit()

    return {
        "incident_id": incident.id,
        "incident_code": incident.incident_code,
        "old_status": old_status,
        "new_status": new_status,
        "released_assignments": released_count,
        "superseded_plans": superseded_plans,
        "superseded_duplicate_reviews": superseded_reviews,
        "allowed_next": ALLOWED_TRANSITIONS.get(new_status, []),
    }