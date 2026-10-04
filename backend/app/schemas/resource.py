from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ResourceType = Literal[
    "ambulance",
    "fire_truck",
    "rescue_team",
    "rescue_boat",
    "police_unit",
    "medical_supplies",
    "relief_supplies",
]


class ResourceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    resource_type: ResourceType
    quantity: int = Field(default=1, ge=1, le=10000)
    available_quantity: int | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=255)
    status: Literal["available", "unavailable"] = "available"

    @model_validator(mode="after")
    def _check(self) -> "ResourceCreate":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both latitude and longitude, or neither")

        if (
            self.available_quantity is not None
            and self.available_quantity > self.quantity
        ):
            raise ValueError("available_quantity cannot be greater than quantity")

        return self


class ResourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    resource_type: ResourceType | None = None
    quantity: int | None = Field(default=None, ge=1, le=10000)
    available_quantity: int | None = Field(default=None, ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    location_name: str | None = Field(default=None, max_length=255)
    status: Literal["available", "unavailable"] | None = None

    @model_validator(mode="after")
    def _check(self) -> "ResourceUpdate":
        lat_sent = "latitude" in self.model_fields_set
        lon_sent = "longitude" in self.model_fields_set

        if lat_sent != lon_sent or (self.latitude is None) != (
            self.longitude is None
        ):
            raise ValueError("Send both latitude and longitude, or neither")

        return self


class ResourceResponse(BaseModel):
    id: int
    name: str
    resource_type: str
    quantity: int
    available_quantity: int
    latitude: float | None
    longitude: float | None
    location_name: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}