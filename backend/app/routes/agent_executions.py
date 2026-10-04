from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent_execution import AgentExecution

router = APIRouter(
    prefix="/api/agent-executions",
    tags=["AI Activity"],
)


@router.get("/")
def get_agent_executions(
    db: Session = Depends(get_db),
):
    executions = (
        db.query(AgentExecution)
        .order_by(AgentExecution.id.desc())
        .limit(100)
        .all()
    )

    result = []

    for execution in executions:
        item = {}

        for column in AgentExecution.__table__.columns:
            value = getattr(execution, column.name, None)

            if hasattr(value, "isoformat"):
                value = value.isoformat()

            item[column.name] = value

        result.append(item)

    return {
        "count": len(result),
        "executions": result,
    }