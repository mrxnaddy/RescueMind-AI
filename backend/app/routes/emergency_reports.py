from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.emergency_report import EmergencyReport
from app.schemas.emergency_report import (
    EmergencyReportCreate,
    EmergencyReportResponse,
    EmergencyReportUpdate,
)

router = APIRouter(
    prefix="/api/emergency-reports",
    tags=["Emergency Reports"],
)


@router.post(
    "/",
    response_model=EmergencyReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_emergency_report(
    report: EmergencyReportCreate,
    db: Session = Depends(get_db),
):
    new_report = EmergencyReport(
        reporter_name=report.reporter_name,
        reporter_phone=report.reporter_phone,
        emergency_type=report.emergency_type,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        address=report.address,
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


@router.get(
    "/",
    response_model=list[EmergencyReportResponse],
)
def get_emergency_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    emergency_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(EmergencyReport)

    if emergency_type:
        query = query.filter(
            EmergencyReport.emergency_type == emergency_type
        )

    reports = (
        query
        .order_by(EmergencyReport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return reports


@router.get(
    "/{report_id}",
    response_model=EmergencyReportResponse,
)
def get_emergency_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = (
        db.query(EmergencyReport)
        .filter(EmergencyReport.id == report_id)
        .first()
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Emergency report not found",
        )

    return report


@router.patch(
    "/{report_id}",
    response_model=EmergencyReportResponse,
)
def update_emergency_report(
    report_id: int,
    report_update: EmergencyReportUpdate,
    db: Session = Depends(get_db),
):
    report = (
        db.query(EmergencyReport)
        .filter(EmergencyReport.id == report_id)
        .first()
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Emergency report not found",
        )

    report.status = report_update.status

    db.commit()
    db.refresh(report)

    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_emergency_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = (
        db.query(EmergencyReport)
        .filter(EmergencyReport.id == report_id)
        .first()
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Emergency report not found",
        )

    db.delete(report)
    db.commit()

    return None