from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.response_plan import ResponsePlan
from app.schemas.plan import DecisionRequest, PlanResponse
from app.services.approval_service import (
    ApprovalError,
    approve_plan,
    reject_plan,
)
from app.services.planning_service import PlanningError, generate_plan

router = APIRouter(
    prefix="/api/plans",
    tags=["Response Plans"],
)


@router.post(
    "/incidents/{incident_id}/generate",
    response_model=PlanResponse,
    status_code=201,
)
def generate_incident_plan(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status in ("merged", "resolved"):
        raise HTTPException(
            status_code=409,
            detail=(
                f"This incident is {incident.status}; "
                "a new plan cannot be generated"
            ),
        )

    try:
        return generate_plan(incident_id, db)
    except PlanningError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/incidents/{incident_id}",
    response_model=list[PlanResponse],
)
def list_incident_plans(
    incident_id: int,
    db: Session = Depends(get_db),
):
    return (
        db.query(ResponsePlan)
        .filter(ResponsePlan.incident_id == incident_id)
        .order_by(ResponsePlan.id.desc())
        .all()
    )


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    plan = (
        db.query(ResponsePlan)
        .filter(ResponsePlan.id == plan_id)
        .first()
    )

    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    return plan


@router.post("/{plan_id}/approve")
def approve_response_plan(
    plan_id: int,
    request: DecisionRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = request.notes if request else None

    try:
        return approve_plan(plan_id, notes, db)
    except ApprovalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/{plan_id}/reject")
def reject_response_plan(
    plan_id: int,
    request: DecisionRequest | None = None,
    db: Session = Depends(get_db),
):
    notes = request.notes if request else None

    try:
        return reject_plan(plan_id, notes, db)
    except ApprovalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)