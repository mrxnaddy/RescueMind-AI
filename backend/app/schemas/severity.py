from pydantic import BaseModel, Field

from app.schemas.intake import Signal


class SeverityTestRequest(BaseModel):
    """Test input for the Severity Agent (same signals the Intake Agent gives)."""

    immediate_threat: Signal = "unknown"
    people_trapped: Signal = "unknown"
    injuries_reported: Signal = "unknown"
    vulnerable_people_involved: Signal = "unknown"
    people_affected_count: int | None = Field(default=None, ge=0)
    key_phrases: list[str] = Field(default_factory=list)