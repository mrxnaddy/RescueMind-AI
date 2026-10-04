from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.resource import Resource
from app.models.resource_assignment import ResourceAssignment
from app.schemas.assignment import AssignmentView
from app.schemas.plan import DecisionRequest
from app.services.approval_service import (
    ApprovalError,
    release_assignment,
    release_incident_assignments,
)

router = APIRouter(
    prefix="/api/assignments",
    tags=["Resource Assignments"],
)


@router.get("/", response_model=list[AssignmentView])
def list_assignments(
    incident_id: int | None = Query(default=None),
    resource_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ResourceAssignment, Resource, Incident)
        .join(Resource, Resource.id == ResourceAssignment.resource_id)
        .join(Incident, Incident.id == ResourceAssignment.incident_id)
    )

    if incident_id is not None:
        query = query.filter(ResourceAssignment.incident_id == incident_id)

    if resource_id is not None:
        query = query.filter(ResourceAssignment.resource_id == resource_id)

    if status:
        query = query.filter(ResourceAssignment.status == status)

    rows = (
        query
        .order_by(ResourceAssignment.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        AssignmentView(
            id=assignment.id,
            incident_id=assignment.incident_id,
            incident_code=incident.incident_code,
            resource_id=assignment.resource_id,
            resource_name=resource.name,
            resource_type=resource.resource_type,
            quantity=assignment.quantity,
            status=assignment.status,
            assigned_at=assignment.assigned_at,
            created_at=assignment.created_at,
        )
        for assignment, resource, incident in rows
    ]


@router.post("/incidents/{incident_id}/release-all")
def release_all_for_incident(
    incident_id: int,
    request: DecisionRequest | None = None,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    notes = request.notes if request else None

    return release_incident_assignments(incident_id, notes, db)


@router.post("/{assignment_id}/release")
def release_one_assignment(
    assignment_id: int,
    request: DecisionRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = request.notes if request else None

    try:
        return release_assignment(assignment_id, notes, db)
    except ApprovalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)