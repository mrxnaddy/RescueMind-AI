from pydantic import BaseModel, Field


class LocationTestRequest(BaseModel):
    """Test input for the Location Agent. No range limits on purpose,
    so we can test invalid coordinates too."""

    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    location_mentions: list[str] = Field(default_factory=list)