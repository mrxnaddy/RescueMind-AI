from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.base import AgentError
from app.agents.intake_agent import IntakeAgent
from app.agents.location_agent import LocationAgent
from app.agents.severity_agent import SeverityAgent
from app.database import get_db
from app.models.emergency_report import EmergencyReport
from app.schemas.agent import AgentResult
from app.schemas.location import LocationTestRequest
from app.schemas.severity import SeverityTestRequest
from app.schemas.analysis import ReportAnalysisResponse
from app.services.analysis_service import analyze_report

router = APIRouter(
    prefix="/api/analysis",
    tags=["Emergency Analysis"],
)


@router.post(
    "/reports/{report_id}/intake",
    response_model=AgentResult,
)
def run_intake_on_report(
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

    input_data = {
        "report_id": report.id,
        "description": report.description,
        "selected_emergency_type": report.emergency_type,
        "address": report.address,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "reported_at": report.created_at.isoformat(),
    }

    agent = IntakeAgent()

    try:
        return agent.run(input_data, db)
    except AgentError as exc:
        raise HTTPException(status_code=502, detail=exc.message)


@router.post(
    "/location/test",
    response_model=AgentResult,
)
def test_location_agent(
    request: LocationTestRequest,
    db: Session = Depends(get_db),
):
    agent = LocationAgent()

    try:
        return agent.run(request.model_dump(), db)
    except AgentError as exc:
        raise HTTPException(status_code=500, detail=exc.message)


@router.post(
    "/severity/test",
    response_model=AgentResult,
)

def test_severity_agent(
    request: SeverityTestRequest,
    db: Session = Depends(get_db),
):
    agent = SeverityAgent()

    try:
        return agent.run(request.model_dump(), db)
    except AgentError as exc:
        raise HTTPException(status_code=500, detail=exc.message)        



@router.post(
    "/reports/{report_id}/analyze",
    response_model=ReportAnalysisResponse,
)
def analyze_emergency_report(
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

    return analyze_report(report, db)