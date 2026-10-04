import time
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.agents.base import AgentError, BaseAgent
from app.models.audit_log import AuditLog
from app.schemas.agent import AgentResult, PipelineResult, PipelineStep


class Orchestrator:
    """Runs agents in order, retries failures, validates output,
    and writes an audit trail."""

    def __init__(
        self,
        agents: list[BaseAgent],
        max_retries: int = 2,
        retry_delay_seconds: float = 0.5,
    ) -> None:
        self.agents = agents
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

    def run(
        self,
        input_data: dict[str, Any],
        db: Session,
        incident_id: int | None = None,
    ) -> PipelineResult:
        steps: list[PipelineStep] = []
        results: dict[str, Any] = {}

        self._audit(
            db,
            "pipeline_started",
            incident_id,
            f"Pipeline started with {len(self.agents)} agents",
            {"agents": [agent.name for agent in self.agents]},
        )

        for agent in self.agents:
            agent_input = {
                **input_data,
                "previous_results": {
                    name: data["output"] for name, data in results.items()
                },
            }

            result, attempts, error = self._run_with_retries(
                agent, agent_input, db, incident_id
            )

            if result is not None:
                error = self._validate(result)

            if result is None or error is not None:
                steps.append(
                    PipelineStep(
                        agent_name=agent.name,
                        status="failed",
                        attempts=attempts,
                        error=error,
                    )
                )
                self._audit(
                    db,
                    "agent_failed",
                    incident_id,
                    f"{agent.name} failed after {attempts} attempt(s): {error}",
                    {"agent": agent.name, "attempts": attempts},
                )
                self._audit(
                    db,
                    "pipeline_failed",
                    incident_id,
                    f"Pipeline stopped at {agent.name}",
                    {"failed_agent": agent.name},
                )
                return PipelineResult(
                    status="failed",
                    steps=steps,
                    results=results,
                    failed_agent=agent.name,
                )

            results[agent.name] = result.model_dump()
            steps.append(
                PipelineStep(
                    agent_name=agent.name,
                    status="completed",
                    attempts=attempts,
                    explanation=result.explanation,
                )
            )
            self._audit(
                db,
                "agent_completed",
                incident_id,
                f"{agent.name} completed in {attempts} attempt(s)",
                {"agent": agent.name, "attempts": attempts},
            )

        self._audit(
            db,
            "pipeline_completed",
            incident_id,
            "Pipeline completed. Human approval is required before any action.",
            {"agents": [agent.name for agent in self.agents]},
        )

        return PipelineResult(
            status="completed",
            steps=steps,
            results=results,
        )

    def _run_with_retries(
        self,
        agent: BaseAgent,
        agent_input: dict[str, Any],
        db: Session,
        incident_id: int | None,
    ) -> tuple[AgentResult | None, int, str | None]:
        total_attempts = self.max_retries + 1
        last_error: str | None = None

        for attempt in range(1, total_attempts + 1):
            try:
                result = agent.run(agent_input, db, incident_id)
                return result, attempt, None
            except AgentError as exc:
                last_error = exc.message

                if attempt < total_attempts:
                    self._audit(
                        db,
                        "agent_retry",
                        incident_id,
                        f"{agent.name} failed on attempt {attempt}; retrying",
                        {
                            "agent": agent.name,
                            "attempt": attempt,
                            "error": last_error,
                        },
                    )
                    time.sleep(self.retry_delay_seconds * attempt)

        return None, total_attempts, last_error

    @staticmethod
    def _validate(result: AgentResult) -> str | None:
        """Return an error message if the agent output is not acceptable."""

        if not result.explanation.strip():
            return "Agent returned no explanation (explainability is required)"

        if not result.output:
            return "Agent returned empty output"

        return None

    @staticmethod
    def _audit(
        db: Session,
        action: str,
        incident_id: int | None,
        description: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        db.add(
            AuditLog(
                user_id=None,
                action=action,
                entity_type="pipeline",
                entity_id=incident_id,
                description=description,
                metadata_json=jsonable_encoder(metadata or {}),
            )
        )
        db.commit()