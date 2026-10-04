from typing import Literal

from pydantic import BaseModel, Field

IncidentStatus = Literal[
    "pending",
    "under_review",
    "approved",
    "assigned",
    "in_progress",
    "resolved",
]


class StatusChangeRequest(BaseModel):
    status: IncidentStatus
    notes: str | None = Field(default=None, max_length=1000)