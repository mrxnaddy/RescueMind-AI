import math
import re
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent import AgentResult


def _clean_text(value: Any) -> str | None:
    """Collapse extra whitespace and trim stray commas/semicolons."""

    if value is None:
        return None

    cleaned = re.sub(r"\s+", " ", str(value)).strip(" ,;")
    return cleaned or None


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return number if math.isfinite(number) else None


def _dedupe(items: list[str | None]) -> list[str]:
    """Remove empty and duplicate items (case-insensitive), keep order."""

    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        if not item:
            continue

        key = item.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result


class LocationAgent(BaseAgent):
    """Validates and normalizes location information (no LLM, no guessing).

    It never invents coordinates. If only an address is available, the
    location is marked for human verification.
    """

    name = "location_agent"

    @staticmethod
    def _validate_coordinates(
        latitude: float | None,
        longitude: float | None,
    ) -> tuple[dict[str, float] | None, list[str]]:
        warnings: list[str] = []

        if latitude is None and longitude is None:
            return None, warnings

        if latitude is None or longitude is None:
            warnings.append(
                "Only one of latitude/longitude was provided; "
                "coordinates were ignored"
            )
            return None, warnings

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            warnings.append(
                "Coordinates are outside the valid range; they were ignored"
            )
            return None, warnings

        if latitude == 0 and longitude == 0:
            warnings.append(
                "Coordinates are exactly 0,0 which is usually a default or "
                "error value; they were ignored"
            )
            return None, warnings

        return {
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
        }, warnings

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        latitude = _to_float(input_data.get("latitude"))
        longitude = _to_float(input_data.get("longitude"))
        address = _clean_text(input_data.get("address"))

        previous = input_data.get("previous_results") or {}
        intake = previous.get("intake_agent") or {}
        raw_mentions = (
            intake.get("location_mentions")
            or input_data.get("location_mentions")
            or []
        )
        mentions = _dedupe([_clean_text(item) for item in raw_mentions])

        coordinates, warnings = self._validate_coordinates(latitude, longitude)

        if coordinates:
            certainty = "coordinates_provided"
        elif address:
            certainty = "address_only"
        elif mentions:
            certainty = "text_mentions_only"
        else:
            certainty = "none"

        needs_verification = certainty != "coordinates_provided"

        missing: list[str] = []

        if certainty in ("address_only", "text_mentions_only"):
            missing.append(
                "Exact coordinates are not available; a coordinator must "
                "verify the location (addresses are not geocoded automatically)"
            )
        elif certainty == "none":
            missing.append("No usable location information provided")

        label = address or (", ".join(mentions) if mentions else None)

        if coordinates:
            coordinate_text = (
                f"{coordinates['latitude']}, {coordinates['longitude']}"
            )
            location_summary = (
                f"{label} ({coordinate_text})" if label else coordinate_text
            )
        else:
            location_summary = label or "Unknown location"

        evidence: list[str] = []

        if coordinates:
            evidence.append(
                "Coordinates supplied by the reporter: "
                f"{coordinates['latitude']}, {coordinates['longitude']}"
            )

        if address:
            evidence.append(f"Address supplied by the reporter: {address}")

        for mention in mentions:
            evidence.append(f"Location mentioned in the report text: {mention}")

        explanations = {
            "coordinates_provided": (
                "Valid coordinates were supplied by the reporter, so the "
                "incident can be shown on the map. No geocoding was needed."
            ),
            "address_only": (
                "Only a text address was supplied. No geocoding service is "
                "configured, so no coordinates were derived or guessed. "
                "A coordinator must verify the location."
            ),
            "text_mentions_only": (
                "Only place names found in the report text are available. "
                "No coordinates were derived or guessed. "
                "A coordinator must verify the location."
            ),
            "none": (
                "No usable location information was found. A coordinator "
                "must obtain the location from the reporter."
            ),
        }

        explanation = explanations[certainty]

        if warnings:
            explanation += " Warnings: " + "; ".join(warnings) + "."

        return AgentResult(
            agent_name=self.name,
            output={
                "location_certainty": certainty,
                "coordinates": coordinates,
                "map_ready": coordinates is not None,
                "normalized_address": address,
                "location_mentions": mentions,
                "location_summary": location_summary,
                "geocoding_status": "not_available",
                "needs_location_verification": needs_verification,
                "warnings": warnings,
            },
            explanation=explanation,
            supporting_evidence=evidence,
            missing_information=missing,
            requires_human_verification=needs_verification,
        )