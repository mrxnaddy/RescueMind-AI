from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents.base import AgentError
from app.agents.echo_agent import EchoAgent
from app.config import settings
from app.database import get_db
from app.models.agent_execution import AgentExecution
from app.schemas.agent import (
    AgentExecutionResponse,
    AgentResult,
    AgentTestRequest,
    LLMTestRequest,
)
from app.services.llm_service import LLMError, LLMService

router = APIRouter(
    prefix="/api/agents",
    tags=["AI Agents"],
)


@router.post("/test", response_model=AgentResult)
def test_agent(
    request: AgentTestRequest,
    db: Session = Depends(get_db),
):
    agent = EchoAgent()

    try:
        return agent.run(request.model_dump(), db)
    except AgentError as exc:
        raise HTTPException(status_code=500, detail=exc.message)


@router.get(
    "/executions",
    response_model=list[AgentExecutionResponse],
)
def list_agent_executions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(AgentExecution)
        .order_by(AgentExecution.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/llm/models")
def list_llm_models():
    try:
        llm = LLMService()
        return {
            "configured_model": settings.GROQ_MODEL,
            "available_models": llm.list_models(),
        }
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/llm/test")
def test_llm(request: LLMTestRequest):
    system_prompt = (
        "You are an emergency report classifier. Classify the report into "
        "exactly one of: flood, earthquake, fire, road_accident, medical. "
        'Return JSON with keys: "emergency_type", "confidence" '
        '(a number from 0 to 1), and "reason" (one short sentence).'
    )

    try:
        llm = LLMService()
        result = llm.generate_json(system_prompt, request.text)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {
        "model": llm.model,
        "result": result,
    }