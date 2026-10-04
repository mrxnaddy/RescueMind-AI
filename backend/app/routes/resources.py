from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.resource import Resource
from app.models.resource_assignment import ResourceAssignment
from app.schemas.resource import (
    ResourceCreate,
    ResourceResponse,
    ResourceType,
    ResourceUpdate,
)
from app.services.resource_service import derive_status

router = APIRouter(
    prefix="/api/resources",
    tags=["Resources"],
)

# These fields can be cleared by sending null.
NULLABLE_FIELDS = {"latitude", "longitude", "location_name"}


def _audit(
    db: Session,
    action: str,
    resource_id: int,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=None,
            action=action,
            entity_type="resource",
            entity_id=resource_id,
            description=description,
            metadata_json=jsonable_encoder(metadata or {}),
        )
    )


def _get_resource(resource_id: int, db: Session) -> Resource:
    resource = (
        db.query(Resource)
        .filter(Resource.id == resource_id)
        .first()
    )

    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource


@router.get("/summary")
def resource_summary(db: Session = Depends(get_db)):
    available_units = func.sum(
        case(
            (Resource.status != "unavailable", Resource.available_quantity),
            else_=0,
        )
    )

    rows = (
        db.query(
            Resource.resource_type,
            func.count(Resource.id),
            func.sum(Resource.quantity),
            available_units,
        )
        .group_by(Resource.resource_type)
        .order_by(Resource.resource_type)
        .all()
    )

    by_type = [
        {
            "resource_type": row[0],
            "resources": int(row[1]),
            "units_total": int(row[2] or 0),
            "units_available": int(row[3] or 0),
        }
        for row in rows
    ]

    return {
        "by_type": by_type,
        "totals": {
            "resources": sum(item["resources"] for item in by_type),
            "units_total": sum(item["units_total"] for item in by_type),
            "units_available": sum(item["units_available"] for item in by_type),
        },
        "note": "All resources are simulated prototype data.",
    }


@router.get("/", response_model=list[ResourceResponse])
def list_resources(
    resource_type: ResourceType | None = Query(default=None),
    status: str | None = Query(default=None),
    available_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Resource)

    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)

    if status:
        query = query.filter(Resource.status == status)

    if available_only:
        query = query.filter(
            Resource.status != "unavailable",
            Resource.available_quantity > 0,
        )

    return (
        query
        .order_by(Resource.resource_type, Resource.name)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/", response_model=ResourceResponse, status_code=201)
def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
):
    available = (
        data.quantity
        if data.available_quantity is None
        else data.available_quantity
    )

    resource = Resource(
        name=data.name.strip(),
        resource_type=data.resource_type,
        quantity=data.quantity,
        available_quantity=available,
        latitude=data.latitude,
        longitude=data.longitude,
        location_name=data.location_name,
        status=derive_status(data.status, available),
    )
    db.add(resource)
    db.flush()

    _audit(
        db,
        "resource_created",
        resource.id,
        f"Resource '{resource.name}' created",
        data.model_dump(),
    )
    db.commit()
    db.refresh(resource)

    return resource


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
):
    return _get_resource(resource_id, db)


@router.patch("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(get_db),
):
    resource = _get_resource(resource_id, db)

    changes = {
        key: value
        for key, value in data.model_dump(exclude_unset=True).items()
        if value is not None or key in NULLABLE_FIELDS
    }

    if not changes:
        raise HTTPException(status_code=400, detail="No fields to update")

    new_quantity = changes.get("quantity", resource.quantity)
    new_available = changes.get("available_quantity", resource.available_quantity)

    if new_available > new_quantity:
        raise HTTPException(
            status_code=422,
            detail="available_quantity cannot be greater than quantity",
        )

    requested_status = changes.pop("status", resource.status)

    for key, value in changes.items():
        setattr(resource, key, value.strip() if key == "name" else value)

    resource.status = derive_status(requested_status, resource.available_quantity)

    _audit(
        db,
        "resource_updated",
        resource.id,
        f"Resource '{resource.name}' updated",
        {"changes": changes, "requested_status": requested_status},
    )
    db.commit()
    db.refresh(resource)

    return resource


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
):
    resource = _get_resource(resource_id, db)

    has_assignments = (
        db.query(ResourceAssignment.id)
        .filter(ResourceAssignment.resource_id == resource_id)
        .first()
        is not None
    )

    if has_assignments:
        raise HTTPException(
            status_code=409,
            detail=(
                "This resource has assignment history and cannot be deleted. "
                "Set its status to 'unavailable' instead."
            ),
        )

    _audit(
        db,
        "resource_deleted",
        resource.id,
        f"Resource '{resource.name}' deleted",
    )
    db.delete(resource)
    db.commit()

    return {"deleted": True, "id": resource_id}