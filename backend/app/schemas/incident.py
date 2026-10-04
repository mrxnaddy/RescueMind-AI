from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IncidentListItem(BaseModel):
    id: int
    incident_code: str
    title: str
    description: str | None
    emergency_type: str
    severity: str
    status: str
    report_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentResponse(IncidentListItem):
    ai_analysis: dict[str, Any] | None = None


class IncidentLocationResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    address: str | None
    location_source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentHistoryResponse(BaseModel):
    id: int
    action: str
    old_value: str | None
    new_value: str | None
    changed_by: int | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentDetailResponse(IncidentResponse):
    locations: list[IncidentLocationResponse] = Field(default_factory=list)
    history: list[IncidentHistoryResponse] = Field(default_factory=list)
    report_ids: list[int] = Field(default_factory=list)