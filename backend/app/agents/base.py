from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.models.agent_execution import AgentExecution
from app.schemas.agent import AgentResult


class AgentError(Exception):
    """Raised when an agent fails. The orchestrator will catch this."""

    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        self.message = message
        super().__init__(f"[{agent_name}] {message}")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseAgent(ABC):
    """Every agent inherits from this class and implements process()."""

    name: str = "base_agent"

    @abstractmethod
    def process(self, input_data: dict[str, Any]) -> AgentResult:
        """The agent's real logic. Must return an AgentResult."""

    def run(
        self,
        input_data: dict[str, Any],
        db: Session,
        incident_id: int | None = None,
    ) -> AgentResult:
        """Runs the agent and logs everything in agent_executions."""

        execution = AgentExecution(
            incident_id=incident_id,
            agent_name=self.name,
            status="started",
            input_data=jsonable_encoder(input_data),
            started_at=_utc_now(),
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        try:
            result = self.process(input_data)

            if not isinstance(result, AgentResult):
                raise TypeError("process() must return an AgentResult")

            result.agent_name = self.name

        except Exception as exc:
            db.rollback()
            execution.status = "failed"
            execution.output_data = {"error": str(exc)}
            execution.explanation = f"Agent failed: {exc}"
            execution.completed_at = _utc_now()
            db.commit()
            raise AgentError(self.name, str(exc)) from exc

        execution.status = "completed"
        execution.output_data = jsonable_encoder(result.model_dump())
        execution.explanation = result.explanation
        execution.completed_at = _utc_now()
        db.commit()

        return result