from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.agents.echo_agent import EchoAgent
from app.agents.sample_agents import FlakyEchoAgent, WordLengthAgent
from app.database import get_db
from app.models.audit_log import AuditLog
from app.orchestrator.orchestrator import Orchestrator
from app.schemas.agent import (
    AuditLogResponse,
    OrchestratorTestRequest,
    PipelineResult,
)

router = APIRouter(
    prefix="/api/orchestrator",
    tags=["Orchestrator"],
)


@router.post("/test", response_model=PipelineResult)
def test_orchestrator(
    request: OrchestratorTestRequest,
    db: Session = Depends(get_db),
):
    if request.scenario == "retry":
        first_agent = FlakyEchoAgent(fail_times=1)
    else:
        first_agent = EchoAgent()

    orchestrator = Orchestrator(
        [first_agent, WordLengthAgent()],
        max_retries=2,
    )

    input_data = {
        "text": request.text,
        "simulate_error": request.scenario == "failure",
    }

    return orchestrator.run(input_data, db)


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
)
def list_audit_logs(
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(limit)
        .all()
    )