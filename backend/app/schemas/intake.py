from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

EMERGENCY_TYPES = (
    "flood",
    "earthquake",
    "fire",
    "road_accident",
    "medical",
    "other",
    "unknown",
)

Signal = Literal["yes", "no", "unknown"]


class IntakeAnalysis(BaseModel):
    """Structured data the Intake Agent extracts from one report.

    Signals use three values: yes, no (only if the report explicitly says so)
    and unknown (the report does not say). Missing information is not the
    same as negative evidence.
    """

    emergency_type: Literal[
        "flood",
        "earthquake",
        "fire",
        "road_accident",
        "medical",
        "other",
        "unknown",
    ] = "unknown"
    summary: str = ""
    people_affected_count: int | None = None
    injuries_reported: Signal = "unknown"
    people_trapped: Signal = "unknown"
    immediate_threat: Signal = "unknown"
    vulnerable_people_involved: Signal = "unknown"
    location_mentions: list[str] = Field(default_factory=list)
    reported_time_text: str | None = None
    key_phrases: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)

    @field_validator("emergency_type", mode="before")
    @classmethod
    def _clean_type(cls, value: Any) -> str:
        cleaned = (
            str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
        )
        return cleaned if cleaned in EMERGENCY_TYPES else "unknown"

    @field_validator("summary", mode="before")
    @classmethod
    def _clean_summary(cls, value: Any) -> str:
        return str(value or "").strip()

    @field_validator("people_affected_count", mode="before")
    @classmethod
    def _clean_count(cls, value: Any) -> int | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number if number >= 0 else None

    @field_validator(
        "injuries_reported",
        "people_trapped",
        "immediate_threat",
        "vulnerable_people_involved",
        mode="before",
    )
    @classmethod
    def _clean_signal(cls, value: Any) -> str:
        if value is True:
            return "yes"
        if value is False:
            return "no"
        cleaned = str(value or "").strip().lower()
        return cleaned if cleaned in ("yes", "no") else "unknown"

    @field_validator("reported_time_text", mode="before")
    @classmethod
    def _clean_time(cls, value: Any) -> str | None:
        if value is None or not str(value).strip():
            return None
        return str(value).strip()

    @field_validator(
        "location_mentions",
        "key_phrases",
        "missing_information",
        mode="before",
    )
    @classmethod
    def _clean_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []