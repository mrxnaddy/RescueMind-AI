from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.emergency_report import EmergencyReport
from app.models.incident import Incident
from app.models.incident_history import IncidentHistory
from app.models.incident_location import IncidentLocation
from app.schemas.incident import (
    IncidentDetailResponse,
    IncidentHistoryResponse,
    IncidentListItem,
    IncidentLocationResponse,
    IncidentResponse,
)

router = APIRouter(
    prefix="/api/incidents",
    tags=["Incidents"],
)


@router.get(
    "/",
    response_model=list[IncidentListItem],
)
def list_incidents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    emergency_type: str | None = Query(default=None),
        include_merged: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    query = db.query(Incident)

    if severity:
        query = query.filter(Incident.severity == severity)

    if status:
        query = query.filter(Incident.status == status)
    elif not include_merged:
        query = query.filter(Incident.status != "merged")

    if emergency_type:
        query = query.filter(Incident.emergency_type == emergency_type)

    return (
        query
        .order_by(Incident.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
)
def get_incident(
    incident_id: int,
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

    locations = (
        db.query(IncidentLocation)
        .filter(IncidentLocation.incident_id == incident_id)
        .order_by(IncidentLocation.id)
        .all()
    )

    history = (
        db.query(IncidentHistory)
        .filter(IncidentHistory.incident_id == incident_id)
        .order_by(IncidentHistory.id)
        .all()
    )

    report_rows = (
        db.query(EmergencyReport.id)
        .filter(EmergencyReport.incident_id == incident_id)
        .order_by(EmergencyReport.id)
        .all()
    )

    return IncidentDetailResponse(
        **IncidentResponse.model_validate(incident).model_dump(),
        locations=[
            IncidentLocationResponse.model_validate(item)
            for item in locations
        ],
        history=[
            IncidentHistoryResponse.model_validate(item)
            for item in history
        ],
        report_ids=[row[0] for row in report_rows],
    )