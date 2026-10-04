from typing import Any

from pydantic import BaseModel

from app.schemas.agent import PipelineResult


class ReportAnalysisResponse(BaseModel):
    report_id: int
    incident_id: int | None = None
    incident_code: str | None = None
    status: str
    summary: dict[str, Any]
    pipeline: PipelineResult
    requires_human_approval: bool = True
    duplicate_check: dict[str, Any] | None = None