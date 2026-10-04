from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.incident_history import IncidentHistory

router = APIRouter(
    prefix="/api/incident-history",
    tags=["Incident History"],
)


@router.get("/{incident_id}")
def get_incident_history(
    incident_id: int,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    history = (
        db.query(IncidentHistory)
        .filter(IncidentHistory.incident_id == incident_id)
        .order_by(IncidentHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "incident_id": incident_id,
        "count": len(history),
        "history": [
            {
                "id": item.id,
                "action": item.action,
                "old_value": item.old_value,
                "new_value": item.new_value,
                "changed_by": item.changed_by,
                "notes": item.notes,
                "created_at": item.created_at,
            }
            for item in history
        ],
        "note": (
            "Incident history contains simulated/prototype workflow "
            "events and AI-derived actions. AI assessments are not "
            "verified emergency facts."
        ),
    }