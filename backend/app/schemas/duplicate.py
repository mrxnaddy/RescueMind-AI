from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EmbeddingTestRequest(BaseModel):
    texts: list[str] = Field(..., min_length=2, max_length=10)


class ReviewRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class ReportBrief(BaseModel):
    id: int
    emergency_type: str
    description: str
    address: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DuplicateIncidentView(BaseModel):
    id: int
    incident_code: str
    title: str
    emergency_type: str
    severity: str
    status: str
    report_count: int
    created_at: datetime
    reports: list[ReportBrief] = Field(default_factory=list)


class DuplicateCandidateView(BaseModel):
    id: int
    similarity: float
    strength: str | None = None
    status: str
    factors: dict[str, Any] | None = None
    review_notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    incident: DuplicateIncidentView
    candidate: DuplicateIncidentView