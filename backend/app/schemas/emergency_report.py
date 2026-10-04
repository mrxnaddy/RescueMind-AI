from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EmergencyReportCreate(BaseModel):
    reporter_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    reporter_phone: str | None = Field(
        default=None,
        max_length=30,
    )

    emergency_type: Literal[
        "flood",
        "earthquake",
        "fire",
        "road_accident",
        "medical",
    ]

    description: str = Field(
        ...,
        min_length=10,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    address: str | None = Field(
        default=None,
        max_length=500,
    )


class EmergencyReportResponse(BaseModel):
    id: int
    reporter_name: str
    reporter_phone: str | None
    emergency_type: str
    description: str
    latitude: float | None
    longitude: float | None
    address: str | None
    status: str = "reviewing"
    created_at: datetime
    incident_id: int | None = None

    model_config = {
        "from_attributes": True
    }


class EmergencyReportUpdate(BaseModel):
    status: Literal[
        "pending",
        "reviewing",
        "confirmed",
        "rejected",
        "resolved",
    ]