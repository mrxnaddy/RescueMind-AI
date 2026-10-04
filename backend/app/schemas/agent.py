from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentResult(BaseModel):
    """Standard output that every agent must return."""

    agent_name: str
    output: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""
    supporting_evidence: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    requires_human_verification: bool = True


class AgentExecutionResponse(BaseModel):
    id: int
    incident_id: int | None
    agent_name: str
    status: str
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    explanation: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class AgentTestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    simulate_error: bool = False


class LLMTestRequest(BaseModel):
    text: str = Field(..., min_length=10)


class PipelineStep(BaseModel):
    agent_name: str
    status: str
    attempts: int
    explanation: str = ""
    error: str | None = None


class PipelineResult(BaseModel):
    status: str
    steps: list[PipelineStep]
    results: dict[str, Any]
    failed_agent: str | None = None
    requires_human_approval: bool = True


class OrchestratorTestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    scenario: Literal["success", "retry", "failure"] = "success"


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    description: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}