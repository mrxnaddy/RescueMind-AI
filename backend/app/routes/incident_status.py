from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.schemas.workflow import StatusChangeRequest
from app.services.incident_status_service import (
    ALLOWED_TRANSITIONS,
    STATUS_MEANING,
    StatusError,
    change_status,
)

router = APIRouter(tags=["Incident Workflow"])


@router.get("/api/workflow/incident-statuses")
def get_incident_workflow():
    """The status rules (so the frontend can show only valid next steps)."""

    return {
        "statuses": [
            {
                "status": status,
                "meaning": STATUS_MEANING[status],
                "allowed_next": allowed,
            }
            for status, allowed in ALLOWED_TRANSITIONS.items()
        ],
        "notes": [
            "'assigned' is set by approving a response plan, not manually.",
            "'merged' is set by confirming a duplicate, not manually.",
            "Resolving an incident releases its assigned resources.",
        ],
    }


@router.patch("/api/incidents/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    request: StatusChangeRequest,
    db: Session = Depends(get_db),
):
    try:
        return change_status(incident_id, request.status, request.notes, db)
    except StatusError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/api/dashboard/stats", tags=["Dashboard"])
def dashboard_stats(db: Session = Depends(get_db)):
    """Counts for the command dashboard. Merged incidents are not counted."""

    status_rows = (
        db.query(Incident.status, func.count(Incident.id))
        .filter(Incident.status != "merged")
        .group_by(Incident.status)
        .all()
    )
    by_status = {status: int(count) for status, count in status_rows}

    severity_rows = (
        db.query(Incident.severity, func.count(Incident.id))
        .filter(Incident.status.notin_(["merged", "resolved"]))
        .group_by(Incident.severity)
        .all()
    )
    active_by_severity = {
        severity: int(count) for severity, count in severity_rows
    }

    urgent = sum(
        active_by_severity.get(level, 0) for level in ("critical", "high")
    )

    return {
        "total_incidents": sum(by_status.values()),
        "pending": by_status.get("pending", 0),
        "under_review": by_status.get("under_review", 0),
        "urgent": urgent,
        "assigned": by_status.get("assigned", 0),
        "in_progress": by_status.get("in_progress", 0),
        "resolved": by_status.get("resolved", 0),
        "by_status": by_status,
        "active_by_severity": active_by_severity,
        "note": (
            "Urgent means critical or high AI severity among incidents that "
            "are not resolved or merged. Merged incidents are not counted."
        ),
    }