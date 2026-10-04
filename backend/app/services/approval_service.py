from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.incident import Incident
from app.models.incident_history import IncidentHistory
from app.models.resource import Resource
from app.models.resource_assignment import ResourceAssignment
from app.models.response_plan import ResponsePlan
from app.services.resource_service import derive_status


class ApprovalError(Exception):
    """A human decision could not be applied (carries an HTTP status code)."""

    def __init__(self, message: str, status_code: int = 409) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def approve_plan(
    plan_id: int,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    """A human approves a proposed plan: assign the resources.

    All-or-nothing. Availability is checked again (with row locks) because it
    may have changed since the plan was proposed.
    """

    plan = (
        db.query(ResponsePlan)
        .filter(ResponsePlan.id == plan_id)
        .with_for_update()
        .first()
    )

    if plan is None:
        raise ApprovalError("Plan not found", 404)

    if plan.status != "proposed":
        raise ApprovalError(
            f"Only a proposed plan can be approved (this plan is {plan.status})",
            409,
        )

    incident = (
        db.query(Incident)
        .filter(Incident.id == plan.incident_id)
        .first()
    )

    if incident is None:
        raise ApprovalError("Incident not found", 404)

    if incident.status in ("merged", "resolved"):
        raise ApprovalError(f"This incident is {incident.status}", 409)

    allocations = (plan.plan or {}).get("proposed_allocations") or []

    needed: dict[int, int] = {}

    for allocation in allocations:
        resource_id = int(allocation["resource_id"])
        needed[resource_id] = needed.get(resource_id, 0) + int(
            allocation["quantity"]
        )

    resources: dict[int, Resource] = {}

    if needed:
        rows = (
            db.query(Resource)
            .filter(Resource.id.in_(list(needed)))
            .order_by(Resource.id)
            .with_for_update()
            .all()
        )
        resources = {row.id: row for row in rows}

    problems: list[str] = []

    for resource_id, quantity in needed.items():
        resource = resources.get(resource_id)

        if resource is None:
            problems.append(f"Resource #{resource_id} no longer exists")
        elif resource.status == "unavailable":
            problems.append(f"{resource.name} is now unavailable")
        elif resource.available_quantity < quantity:
            problems.append(
                f"{resource.name}: needs {quantity}, only "
                f"{resource.available_quantity} available now"
            )

    if problems:
        db.rollback()
        raise ApprovalError(
            "The plan can no longer be fulfilled because resource "
            "availability changed: "
            + "; ".join(problems)
            + ". Nothing was assigned. Generate a new plan.",
            409,
        )

    now = _utc_now()

    assignments: list[ResourceAssignment] = []

    for allocation in allocations:
        assignment = ResourceAssignment(
            incident_id=incident.id,
            resource_id=int(allocation["resource_id"]),
            quantity=int(allocation["quantity"]),
            status="assigned",
            assigned_by=None,
            assigned_at=now,
        )
        db.add(assignment)
        assignments.append(assignment)

    resource_changes: list[dict[str, Any]] = []

    for resource_id, quantity in needed.items():
        resource = resources[resource_id]
        before = resource.available_quantity

        resource.available_quantity = before - quantity
        resource.status = derive_status(
            resource.status,
            resource.available_quantity,
        )

        resource_changes.append(
            {
                "resource_id": resource.id,
                "name": resource.name,
                "available_before": before,
                "available_after": resource.available_quantity,
                "status": resource.status,
            }
        )

    old_status = incident.status
    new_status = old_status

    if old_status in ("pending", "under_review", "approved"):
        new_status = "assigned" if assignments else "approved"
        incident.status = new_status

    plan.status = "approved"
    plan.reviewed_at = now
    plan.review_notes = notes

    db.flush()

    db.add(
        IncidentHistory(
            incident_id=incident.id,
            action="response_plan_approved",
            new_value=f"plan #{plan.id}",
            notes=(
                f"A human approved the plan. {len(assignments)} assignment(s) "
                "created."
            ),
        )
    )

    if new_status != old_status:
        db.add(
            IncidentHistory(
                incident_id=incident.id,
                action="status_changed",
                old_value=old_status,
                new_value=new_status,
                notes="Changed after plan approval",
            )
        )

    assignment_ids = [assignment.id for assignment in assignments]

    db.add(
        AuditLog(
            user_id=None,
            action="response_plan_approved",
            entity_type="incident",
            entity_id=incident.id,
            description=(
                f"Human approved plan #{plan.id} for {incident.incident_code}"
            ),
            metadata_json=jsonable_encoder(
                {
                    "plan_id": plan.id,
                    "assignment_ids": assignment_ids,
                    "resource_changes": resource_changes,
                    "notes": notes,
                }
            ),
        )
    )

    result_assignments = [
        {
            "id": assignment.id,
            "resource_id": assignment.resource_id,
            "resource_name": resources[assignment.resource_id].name,
            "resource_type": resources[assignment.resource_id].resource_type,
            "quantity": assignment.quantity,
            "status": assignment.status,
        }
        for assignment in assignments
    ]

    db.commit()

    return {
        "status": "approved",
        "plan_id": plan.id,
        "incident": {
            "id": incident.id,
            "incident_code": incident.incident_code,
            "status": incident.status,
        },
        "assignments": result_assignments,
        "resources_updated": resource_changes,
        "note": (
            "Resources are now assigned (simulated). Nothing is dispatched "
            "to real services."
        ),
    }


def reject_plan(
    plan_id: int,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    """A human rejects a proposed plan. No resource is touched."""

    plan = (
        db.query(ResponsePlan)
        .filter(ResponsePlan.id == plan_id)
        .with_for_update()
        .first()
    )

    if plan is None:
        raise ApprovalError("Plan not found", 404)

    if plan.status != "proposed":
        raise ApprovalError(
            f"Only a proposed plan can be rejected (this plan is {plan.status})",
            409,
        )

    plan.status = "rejected"
    plan.reviewed_at = _utc_now()
    plan.review_notes = notes

    db.add(
        IncidentHistory(
            incident_id=plan.incident_id,
            action="response_plan_rejected",
            new_value=f"plan #{plan.id}",
            notes="A human rejected the proposed plan. No resource was assigned.",
        )
    )
    db.add(
        AuditLog(
            user_id=None,
            action="response_plan_rejected",
            entity_type="incident",
            entity_id=plan.incident_id,
            description=f"Human rejected plan #{plan.id}",
            metadata_json=jsonable_encoder(
                {"plan_id": plan.id, "notes": notes}
            ),
        )
    )
    db.commit()

    return {
        "status": "rejected",
        "plan_id": plan.id,
        "note": "No resource was assigned or changed.",
    }


def release_assignment(
    assignment_id: int,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    """Give the units of one assignment back to the resource."""

    assignment = (
        db.query(ResourceAssignment)
        .filter(ResourceAssignment.id == assignment_id)
        .with_for_update()
        .first()
    )

    if assignment is None:
        raise ApprovalError("Assignment not found", 404)

    if assignment.status != "assigned":
        raise ApprovalError(
            "Only an assigned resource can be released "
            f"(status: {assignment.status})",
            409,
        )

    resource = (
        db.query(Resource)
        .filter(Resource.id == assignment.resource_id)
        .with_for_update()
        .first()
    )

    resource_name = "unknown resource"
    available_after = None

    if resource is not None:
        resource_name = resource.name
        resource.available_quantity = min(
            resource.quantity,
            resource.available_quantity + assignment.quantity,
        )
        resource.status = derive_status(
            resource.status,
            resource.available_quantity,
        )
        available_after = resource.available_quantity

    assignment.status = "released"

    
    # If nothing is assigned any more, the incident is no longer "assigned".
    db.flush()

    still_assigned = (
        db.query(ResourceAssignment.id)
        .filter(
            ResourceAssignment.incident_id == assignment.incident_id,
            ResourceAssignment.status == "assigned",
        )
        .first()
    )
    incident = (
        db.query(Incident)
        .filter(Incident.id == assignment.incident_id)
        .first()
    )

    if (
        still_assigned is None
        and incident is not None
        and incident.status == "assigned"
    ):
        incident.status = "approved"
    db.add(
            IncidentHistory(
                incident_id=incident.id,
                action="status_changed",
                old_value="assigned",
                new_value="approved",
                notes="All assigned resources were released",
            )
        )

    db.add(
        IncidentHistory(
            incident_id=assignment.incident_id,
            action="resource_released",
            new_value=resource_name,
            notes=(
                f"{assignment.quantity} unit(s) of {resource_name} were "
                "released back to availability."
            ),
        )
    )
    db.add(
        AuditLog(
            user_id=None,
            action="resource_released",
            entity_type="incident",
            entity_id=assignment.incident_id,
            description=f"Assignment #{assignment.id} released",
            metadata_json=jsonable_encoder(
                {
                    "assignment_id": assignment.id,
                    "resource_id": assignment.resource_id,
                    "quantity": assignment.quantity,
                    "notes": notes,
                }
            ),
        )
    )
    db.commit()

    return {
        "status": "released",
        "assignment_id": assignment.id,
        "resource_name": resource_name,
        "quantity_returned": assignment.quantity,
        "available_after": available_after,
    }


def release_incident_assignments(
    incident_id: int,
    notes: str | None,
    db: Session,
) -> dict[str, Any]:
    """Release every assigned resource of one incident."""

    active_ids = [
        row[0]
        for row in (
            db.query(ResourceAssignment.id)
            .filter(
                ResourceAssignment.incident_id == incident_id,
                ResourceAssignment.status == "assigned",
            )
            .order_by(ResourceAssignment.id)
            .all()
        )
    ]

    released = [
        release_assignment(assignment_id, notes, db)
        for assignment_id in active_ids
    ]

    return {
        "incident_id": incident_id,
        "released_count": len(released),
        "released": released,
    }