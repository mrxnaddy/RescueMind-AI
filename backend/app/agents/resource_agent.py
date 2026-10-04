from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.models.incident import Incident
from app.models.incident_location import IncidentLocation
from app.models.resource import Resource
from app.schemas.agent import AgentResult
from app.utils.geo import haversine_km

# ---------------------------------------------------------------------------
# Transparent, predefined requirement rules. Edit the values here to change them.
#
# when:
#   always                 -> always needed
#   injuries_reported      -> only if the report says injuries = yes
#   injuries_not_ruled_out -> injuries = yes or unknown (not stated)
#   people_trapped         -> only if the report says people are trapped
#
# quantity "affected_people" -> one unit per affected person if the number is
# stated, otherwise DEFAULT_RELIEF_KITS (a planning default, flagged in output).
# scale_critical -> one extra unit when the incident severity is critical.
# ---------------------------------------------------------------------------
RULES_VERSION = "v1"
DEFAULT_RELIEF_KITS = 10

REQUIREMENT_RULES: dict[str, list[dict[str, Any]]] = {
    "flood": [
        {
            "resource_type": "rescue_boat",
            "quantity": 1,
            "when": "always",
            "scale_critical": True,
            "reason": "Boats are used to reach people in flood water",
        },
        {
            "resource_type": "rescue_team",
            "quantity": 1,
            "when": "always",
            "scale_critical": False,
            "reason": "A trained team is needed to evacuate people safely",
        },
        {
            "resource_type": "relief_supplies",
            "quantity": "affected_people",
            "when": "always",
            "scale_critical": False,
            "reason": "Food and water kits for affected people",
        },
        {
            "resource_type": "ambulance",
            "quantity": 1,
            "when": "injuries_reported",
            "scale_critical": False,
            "reason": "Injuries are reported",
        },
    ],
    "fire": [
        {
            "resource_type": "fire_truck",
            "quantity": 1,
            "when": "always",
            "scale_critical": True,
            "reason": "Fire suppression",
        },
        {
            "resource_type": "ambulance",
            "quantity": 1,
            "when": "injuries_reported",
            "scale_critical": False,
            "reason": "Injuries are reported",
        },
        {
            "resource_type": "rescue_team",
            "quantity": 1,
            "when": "people_trapped",
            "scale_critical": False,
            "reason": "People are reported trapped",
        },
    ],
    "road_accident": [
        {
            "resource_type": "ambulance",
            "quantity": 1,
            "when": "injuries_not_ruled_out",
            "scale_critical": True,
            "reason": "Injuries are reported or not ruled out",
        },
        {
            "resource_type": "police_unit",
            "quantity": 1,
            "when": "always",
            "scale_critical": False,
            "reason": "Scene and traffic control",
        },
        {
            "resource_type": "rescue_team",
            "quantity": 1,
            "when": "people_trapped",
            "scale_critical": False,
            "reason": "People are reported trapped (extrication)",
        },
    ],
    "medical": [
        {
            "resource_type": "ambulance",
            "quantity": 1,
            "when": "always",
            "scale_critical": True,
            "reason": "Medical emergency response",
        },
    ],
    "earthquake": [
        {
            "resource_type": "rescue_team",
            "quantity": 2,
            "when": "always",
            "scale_critical": True,
            "reason": "Search and rescue",
        },
        {
            "resource_type": "ambulance",
            "quantity": 1,
            "when": "injuries_not_ruled_out",
            "scale_critical": False,
            "reason": "Injuries are reported or not ruled out",
        },
        {
            "resource_type": "relief_supplies",
            "quantity": "affected_people",
            "when": "always",
            "scale_critical": False,
            "reason": "Water, food and shelter kits for affected people",
        },
        {
            "resource_type": "medical_supplies",
            "quantity": 5,
            "when": "injuries_not_ruled_out",
            "scale_critical": False,
            "reason": "First-aid kits",
        },
    ],
}


def _condition_met(condition: str, signals: dict[str, str]) -> bool:
    if condition == "always":
        return True

    if condition == "injuries_reported":
        return signals["injuries_reported"] == "yes"

    if condition == "injuries_not_ruled_out":
        return signals["injuries_reported"] in ("yes", "unknown")

    if condition == "people_trapped":
        return signals["people_trapped"] == "yes"

    return False


class ResourceMatchingAgent(BaseAgent):
    """Suggests resources for an incident (no LLM, no dispatching).

    It never reserves or changes any resource. A human must approve first.
    """

    name = "resource_matching_agent"

    def __init__(self, db: Session) -> None:
        self.db = db

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        incident_id = input_data.get("incident_id")

        incident = (
            self.db.query(Incident)
            .filter(Incident.id == incident_id)
            .first()
        )

        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        analysis = incident.ai_analysis or {}
        results = analysis.get("results") or {}
        intake = (results.get("intake_agent") or {}).get("output") or {}
        analysis_summary = analysis.get("summary") or {}

        signals = {
            name: str(intake.get(name, "unknown"))
            for name in ("injuries_reported", "people_trapped", "immediate_threat")
        }
        people_count = intake.get("people_affected_count")
        severity = incident.severity or "unknown"

        location = (
            self.db.query(IncidentLocation)
            .filter(IncidentLocation.incident_id == incident.id)
            .order_by(IncidentLocation.id)
            .first()
        )

        warnings: list[str] = []
        assumptions: list[str] = []

        # 1. Work out what the incident needs.
        rules = REQUIREMENT_RULES.get(incident.emergency_type, [])
        requirements: list[dict[str, Any]] = []

        for rule in rules:
            if not _condition_met(rule["when"], signals):
                continue

            quantity = rule["quantity"]

            if quantity == "affected_people":
                if (
                    isinstance(people_count, int)
                    and not isinstance(people_count, bool)
                    and people_count > 0
                ):
                    quantity = people_count
                else:
                    quantity = DEFAULT_RELIEF_KITS
                    assumption = (
                        "Number of affected people is not stated; "
                        f"{DEFAULT_RELIEF_KITS} relief kits were used as a "
                        "planning default"
                    )

                    if assumption not in assumptions:
                        assumptions.append(assumption)

            if severity == "critical" and rule["scale_critical"]:
                quantity += 1

            if (
                rule["when"] == "injuries_not_ruled_out"
                and signals["injuries_reported"] == "unknown"
            ):
                assumption = (
                    "Injuries are not stated; "
                    f"{rule['resource_type']} is suggested as a precaution"
                )

                if assumption not in assumptions:
                    assumptions.append(assumption)

            requirements.append(
                {
                    "resource_type": rule["resource_type"],
                    "quantity_needed": quantity,
                    "reason": rule["reason"],
                }
            )

        if not rules:
            warnings.append(
                f"No automatic resource rules exist for emergency type "
                f"'{incident.emergency_type}'; a coordinator must define the "
                "requirements"
            )

        if severity == "unknown":
            warnings.append(
                "Severity could not be assessed; base quantities were used"
            )

        if analysis_summary.get("type_mismatch"):
            warnings.append(
                f"The reporter selected '{incident.emergency_type}' but the AI "
                f"suggests '{analysis_summary.get('emergency_type')}'. "
                "Requirements follow the reporter's category; please verify."
            )

        if location is None:
            warnings.append(
                "This incident has no verified coordinates: resources are "
                "ranked by free units, not by distance. Verify the location "
                "before approving."
            )

        # 2. Find available resources of the needed types.
        needed_types = {item["resource_type"] for item in requirements}

        pool: list[Resource] = []

        if needed_types:
            pool = (
                self.db.query(Resource)
                .filter(
                    Resource.resource_type.in_(needed_types),
                    Resource.status != "unavailable",
                    Resource.available_quantity > 0,
                )
                .all()
            )

        radius = settings.RESOURCE_SEARCH_RADIUS_KM
        out_of_range: set[int] = set()

        recommendations: list[dict[str, Any]] = []
        unmet: list[dict[str, Any]] = []
        evidence: list[str] = []

        # 3. Match each requirement.
        for requirement in requirements:
            ranked: list[tuple[Resource, float | None]] = []

            for resource in pool:
                if resource.resource_type != requirement["resource_type"]:
                    continue

                distance = None

                if (
                    location is not None
                    and resource.latitude is not None
                    and resource.longitude is not None
                ):
                    distance = haversine_km(
                        location.latitude,
                        location.longitude,
                        resource.latitude,
                        resource.longitude,
                    )

                    if distance > radius:
                        out_of_range.add(resource.id)
                        continue

                ranked.append((resource, distance))

            if location is not None:
                ranked.sort(
                    key=lambda item: (
                        item[1] is None,
                        item[1] if item[1] is not None else 0.0,
                        -item[0].available_quantity,
                        item[0].name,
                    )
                )
            else:
                ranked.sort(
                    key=lambda item: (-item[0].available_quantity, item[0].name)
                )

            remaining = requirement["quantity_needed"]
            allocations: list[dict[str, Any]] = []

            for index, (resource, distance) in enumerate(ranked):
                if remaining <= 0:
                    break

                take = min(remaining, resource.available_quantity)

                if distance is not None:
                    if index == 0:
                        reason = (
                            f"Closest available site ({round(distance, 2)} km) "
                            f"with {resource.available_quantity} unit(s) free"
                        )
                    else:
                        reason = (
                            f"Next closest site ({round(distance, 2)} km), "
                            "used to cover the remaining need"
                        )
                elif location is None:
                    reason = (
                        "Incident location is not verified, so this site was "
                        "ranked by free units only"
                    )
                else:
                    reason = (
                        "Distance unknown because this resource has no "
                        "coordinates"
                    )

                allocations.append(
                    {
                        "resource_id": resource.id,
                        "name": resource.name,
                        "location_name": resource.location_name,
                        "quantity": take,
                        "available_at_site": resource.available_quantity,
                        "distance_km": (
                            None if distance is None else round(distance, 2)
                        ),
                        "reason": reason,
                    }
                )
                remaining -= take

                evidence.append(
                    f"{resource.name}: {take} x {resource.resource_type}"
                    + (
                        ""
                        if distance is None
                        else f", {round(distance, 2)} km"
                    )
                )

            matched = requirement["quantity_needed"] - remaining

            if remaining == 0:
                match_status = "fully_matched"
            elif matched > 0:
                match_status = "partially_matched"
            else:
                match_status = "unmatched"

            if remaining > 0:
                unmet.append(
                    {
                        "resource_type": requirement["resource_type"],
                        "needed": requirement["quantity_needed"],
                        "matched": matched,
                        "short_by": remaining,
                    }
                )

            recommendations.append(
                {
                    "resource_type": requirement["resource_type"],
                    "quantity_needed": requirement["quantity_needed"],
                    "quantity_matched": matched,
                    "match_status": match_status,
                    "requirement_reason": requirement["reason"],
                    "allocations": allocations,
                }
            )

        if out_of_range:
            warnings.append(
                f"{len(out_of_range)} resource site(s) were excluded because "
                f"they are more than {radius} km away"
            )

        # 4. Explanation.
        fully = sum(
            1 for item in recommendations if item["match_status"] == "fully_matched"
        )
        partial = sum(
            1
            for item in recommendations
            if item["match_status"] == "partially_matched"
        )
        none_matched = len(recommendations) - fully - partial

        if requirements:
            explanation = (
                f"Proposed resources for {incident.emergency_type} incident "
                f"{incident.incident_code}: {fully} of {len(requirements)} "
                f"requirement(s) fully matched, {partial} partially, "
                f"{none_matched} unmatched. Nothing has been dispatched or "
                "reserved; a human must approve any assignment."
            )
        else:
            explanation = (
                "No resources were proposed because no automatic requirements "
                "apply to this incident. A coordinator must decide what is "
                "needed. Nothing has been dispatched or reserved."
            )

        missing: list[str] = []

        for item in unmet:
            missing.append(
                f"Not enough available {item['resource_type']}: needed "
                f"{item['needed']}, matched {item['matched']}"
            )

        if location is None:
            missing.append("Verified incident coordinates are missing")

        for name, value in signals.items():
            if value == "unknown":
                missing.append(
                    f"Not stated in the report: {name.replace('_', ' ')}"
                )

        return AgentResult(
            agent_name=self.name,
            output={
                "incident_id": incident.id,
                "incident_code": incident.incident_code,
                "emergency_type_used": incident.emergency_type,
                "severity_used": severity,
                "location_basis": (
                    "coordinates" if location is not None else "unverified"
                ),
                "requirements": requirements,
                "recommendations": recommendations,
                "unmet": unmet,
                "assumptions": assumptions,
                "warnings": warnings,
                "notes": [
                    "Recommendations do not reserve any resources. "
                    "Availability is checked again when a human approves."
                ],
                "rules_version": RULES_VERSION,
                "search_radius_km": radius,
            },
            explanation=explanation,
            supporting_evidence=evidence,
            missing_information=missing,
            requires_human_verification=True,
        )