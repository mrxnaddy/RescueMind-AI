import json
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.duplicate_candidate import DuplicateCandidate
from app.models.incident import Incident
from app.schemas.agent import AgentResult
from app.services.llm_service import LLMService

PLAN_VERSION = "v1"

# One generic coordination step per emergency type (fixed templates).
TYPE_ACTIONS = {
    "flood": (
        "Coordinate boat and rescue team access routes and agree a safe "
        "drop-off point."
    ),
    "fire": (
        "Establish a safe perimeter around the fire before rescue teams enter."
    ),
    "road_accident": (
        "Secure the scene and manage traffic before extrication or medical work."
    ),
    "medical": (
        "Collect the patient's condition and exact address from the reporter "
        "while the ambulance is on the way."
    ),
    "earthquake": (
        "Treat damaged structures as unsafe and coordinate search and rescue "
        "with structural safety in mind."
    ),
}

BRIEFING_SYSTEM_PROMPT = """You write a short briefing for an emergency coordinator.
Use ONLY the facts in the JSON provided. Never add facts, numbers, names or locations
that are not in it. Say clearly when something is unknown or unverified.
Do not give medical or operational orders. Write 3 to 5 plain sentences in English.
Return a JSON object: {"briefing": "<text>"}"""

NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?")


class ResponsePlanningAgent(BaseAgent):
    """Builds a proposed response plan from the other agents' results.

    The plan is deterministic. Only the short coordinator briefing is written
    by the LLM, and it is discarded if it contains numbers that are not in
    the data. Nothing is dispatched: a human must approve the plan.
    """

    name = "response_planning_agent"

    def __init__(self, db: Session, llm: LLMService | None = None) -> None:
        self.db = db
        self._llm = llm

    def _pending_duplicates(self, incident_id: int) -> list[str]:
        rows = (
            self.db.query(DuplicateCandidate)
            .filter(
                DuplicateCandidate.status == "pending",
                or_(
                    DuplicateCandidate.incident_id == incident_id,
                    DuplicateCandidate.candidate_incident_id == incident_id,
                ),
            )
            .all()
        )

        other_ids = [
            row.candidate_incident_id
            if row.incident_id == incident_id
            else row.incident_id
            for row in rows
        ]

        if not other_ids:
            return []

        codes = (
            self.db.query(Incident.incident_code)
            .filter(Incident.id.in_(other_ids))
            .order_by(Incident.id)
            .all()
        )

        return [code for (code,) in codes]

    @staticmethod
    def _build_actions(
        emergency_type: str,
        signals: dict[str, str],
        location_needs_check: bool,
        duplicate_codes: list[str],
    ) -> list[str]:
        actions: list[str] = []

        if duplicate_codes:
            actions.append(
                "Review the possible duplicate report(s) "
                f"({', '.join(duplicate_codes)}) first, so resources are not "
                "sent twice for the same event."
            )

        if location_needs_check:
            actions.append(
                "Verify the exact incident location with the reporter before "
                "any resource leaves its station."
            )

        if signals["people_trapped"] == "yes":
            actions.append(
                "Treat trapped people as the top priority and dispatch rescue "
                "capability first."
            )

        if signals["injuries_reported"] == "yes":
            actions.append(
                "Prepare medical support and confirm a hospital destination."
            )

        if signals["vulnerable_people_involved"] == "yes":
            actions.append(
                "Prioritise children, elderly or disabled people during the "
                "response."
            )

        if signals["immediate_threat"] == "yes":
            actions.append(
                "The report describes an ongoing danger; keep in contact with "
                "the reporter for updates."
            )

        type_action = TYPE_ACTIONS.get(emergency_type)

        if type_action:
            actions.append(type_action)

        actions.append(
            "Re-check resource availability and the latest incident "
            "information immediately before approving the plan."
        )

        return actions

    def _write_briefing(
        self,
        facts: dict[str, Any],
    ) -> tuple[str | None, str | None]:
        """Return (briefing, note). The note explains why there is no briefing."""

        facts_text = json.dumps(facts, ensure_ascii=False)

        try:
            if self._llm is None:
                self._llm = LLMService()

            result = self._llm.generate_json(
                BRIEFING_SYSTEM_PROMPT,
                "Facts:\n" + facts_text,
            )
        except Exception as exc:
            return None, f"The AI briefing could not be generated: {exc}"

        briefing = str(result.get("briefing") or "").strip()

        if not briefing:
            return None, "The AI briefing was empty"

        allowed = set(NUMBER_PATTERN.findall(facts_text))
        unexpected = [
            number
            for number in NUMBER_PATTERN.findall(briefing)
            if number not in allowed
        ]

        if unexpected:
            return None, (
                "The AI briefing was discarded because it contained numbers "
                f"that are not in the data: {unexpected}"
            )

        return briefing, None

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        incident_id = input_data.get("incident_id")

        incident = (
            self.db.query(Incident)
            .filter(Incident.id == incident_id)
            .first()
        )

        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        matching = (input_data.get("previous_results") or {}).get(
            "resource_matching_agent"
        )

        if not matching:
            raise ValueError("Resource matching output is missing")

        analysis = incident.ai_analysis or {}
        results = analysis.get("results") or {}
        analysis_summary = analysis.get("summary") or {}
        intake = (results.get("intake_agent") or {}).get("output") or {}
        location = (results.get("location_agent") or {}).get("output") or {}
        severity_output = (results.get("severity_agent") or {}).get("output") or {}

        signals = {
            name: str(intake.get(name, "unknown"))
            for name in (
                "injuries_reported",
                "people_trapped",
                "immediate_threat",
                "vulnerable_people_involved",
            )
        }

        duplicate_codes = self._pending_duplicates(incident.id)
        location_needs_check = bool(
            location.get("needs_location_verification", True)
        )

        allocations: list[dict[str, Any]] = []

        for recommendation in matching.get("recommendations") or []:
            for allocation in recommendation.get("allocations") or []:
                allocations.append(
                    {
                        "resource_id": allocation["resource_id"],
                        "name": allocation["name"],
                        "resource_type": recommendation["resource_type"],
                        "quantity": allocation["quantity"],
                        "location_name": allocation.get("location_name"),
                        "distance_km": allocation.get("distance_km"),
                        "reason": allocation["reason"],
                    }
                )

        unmet = matching.get("unmet") or []

        verify: list[str] = []
        seen: set[str] = set()

        def add_to_verify(item: str) -> None:
            key = item.strip().lower()

            if key and key not in seen:
                seen.add(key)
                verify.append(item)

        for item in analysis_summary.get("missing_information") or []:
            add_to_verify(item)

        for item in unmet:
            add_to_verify(
                f"Not enough available {item['resource_type']}: needed "
                f"{item['needed']}, matched {item['matched']}"
            )

        if location_needs_check:
            add_to_verify("Incident location must be verified by a coordinator")

        for code in duplicate_codes:
            add_to_verify(f"Possible duplicate of {code} is awaiting human review")

        warnings = list(matching.get("warnings") or [])

        if not analysis:
            warnings.append(
                "AI analysis is not available for this incident; the plan is "
                "based on limited information."
            )

        actions = self._build_actions(
            incident.emergency_type,
            signals,
            location_needs_check,
            duplicate_codes,
        )

        facts = {
            "incident_code": incident.incident_code,
            "emergency_type": incident.emergency_type,
            "severity": incident.severity,
            "severity_score": severity_output.get("score"),
            "ai_summary": intake.get("summary"),
            "people_affected_count": intake.get("people_affected_count"),
            **signals,
            "location": location.get("location_summary"),
            "location_certainty": location.get("location_certainty"),
            "reports_received": incident.report_count,
            "proposed_resources": [
                {
                    "name": item["name"],
                    "type": item["resource_type"],
                    "quantity": item["quantity"],
                }
                for item in allocations
            ],
            "unmet_requirements": unmet,
            "information_to_verify": verify,
            "possible_duplicates_pending": duplicate_codes,
        }

        briefing, briefing_note = self._write_briefing(facts)

        sites = {item["resource_id"] for item in allocations}

        explanation = (
            f"Proposed response plan for {incident.incident_code} "
            f"({incident.emergency_type}, priority {incident.severity}). "
            f"It proposes {len(allocations)} allocation(s) from {len(sites)} "
            f"site(s) and lists {len(verify)} item(s) to verify. This is only "
            "a proposal built from AI-extracted, unverified report "
            "information; nothing is dispatched or reserved until a human "
            "approves it."
        )

        plan = {
            "plan_version": PLAN_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "incident": {
                "id": incident.id,
                "incident_code": incident.incident_code,
                "title": incident.title,
                "emergency_type": incident.emergency_type,
                "severity": incident.severity,
                "severity_score": severity_output.get("score"),
                "status": incident.status,
                "report_count": incident.report_count,
            },
            "situation": {
                "ai_summary": intake.get("summary"),
                "people_affected_count": intake.get("people_affected_count"),
                **signals,
                "location_summary": location.get("location_summary"),
                "location_certainty": location.get("location_certainty"),
                "map_ready": location.get("map_ready"),
                "location_needs_verification": location_needs_check,
            },
            "priority": incident.severity,
            "required_resources": matching.get("requirements") or [],
            "proposed_allocations": allocations,
            "unmet_requirements": unmet,
            "actions": [
                {"order": index, "action": action}
                for index, action in enumerate(actions, start=1)
            ],
            "information_to_verify": verify,
            "pending_duplicate_reviews": duplicate_codes,
            "assumptions": matching.get("assumptions") or [],
            "warnings": warnings,
            "coordinator_briefing": briefing,
            "briefing_note": briefing_note,
            "explanation": explanation,
            "approval": {
                "required": True,
                "status": "proposed",
                "note": (
                    "A human must approve this plan before any resource is "
                    "assigned."
                ),
            },
        }

        evidence = [
            f"{item['name']}: {item['quantity']} x {item['resource_type']}"
            for item in allocations
        ]

        return AgentResult(
            agent_name=self.name,
            output=plan,
            explanation=explanation,
            supporting_evidence=evidence,
            missing_information=verify,
            requires_human_verification=True,
        )