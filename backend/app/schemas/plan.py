from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlanResponse(BaseModel):
    id: int
    incident_id: int
    status: str
    plan: dict[str, Any]
    review_notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)