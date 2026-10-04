from typing import Any

from app.agents.base import BaseAgent
from app.schemas.agent import AgentResult

# ---------------------------------------------------------------------------
# Transparent, predefined scoring rules. Edit the values here to change them.
# ---------------------------------------------------------------------------
RULES_VERSION = "v1"

# (field name in Intake output, label, points if the report says "yes")
SIGNAL_CRITERIA = [
    ("immediate_threat", "Immediate threat reported", 30),
    ("people_trapped", "People trapped", 30),
    ("injuries_reported", "Injuries reported", 30),
    (
        "vulnerable_people_involved",
        "Vulnerable people involved (children, elderly, etc.)",
        15,
    ),
]

# (minimum number of people affected, points) - checked from top to bottom
COUNT_TIERS = [(10, 20), (3, 10), (1, 5)]

MAX_SCORE = 100

# (category, minimum score) - checked from top to bottom
CATEGORY_THRESHOLDS = [
    ("critical", 60),
    ("high", 30),
    ("medium", 15),
    ("low", 1),
]

URGENCY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}


class SeverityAgent(BaseAgent):
    """Rule-based urgency assessment (no LLM).

    Uses only what the report states. Missing information (unknown) is never
    treated as negative evidence (no).
    """

    name = "severity_agent"

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        previous = input_data.get("previous_results") or {}
        source = previous.get("intake_agent") or input_data

        criteria: list[dict[str, Any]] = []
        missing: list[str] = []
        negative: list[str] = []
        score = 0

        for field, label, points in SIGNAL_CRITERIA:
            value = str(source.get(field, "unknown")).strip().lower()

            if value == "yes":
                status, earned = "met", points
            elif value == "no":
                status, earned = "not_met", 0
                negative.append(f"Report explicitly indicates NO for: {label}")
            else:
                value, status, earned = "unknown", "unknown", 0
                missing.append(f"Not stated in the report: {label.lower()}")

            score += earned
            criteria.append(
                {
                    "criterion": label,
                    "reported_value": value,
                    "status": status,
                    "points": earned,
                    "max_points": points,
                }
            )

        raw_count = source.get("people_affected_count")

        try:
            count = (
                None
                if raw_count is None or isinstance(raw_count, bool)
                else int(raw_count)
            )
        except (TypeError, ValueError):
            count = None

        count_points = 0

        if count is None:
            missing.append("Not stated in the report: number of people affected")
        else:
            for minimum, points in COUNT_TIERS:
                if count >= minimum:
                    count_points = points
                    break

        score += count_points
        criteria.append(
            {
                "criterion": "Number of people affected",
                "reported_value": count,
                "status": "unknown" if count is None else "known",
                "points": count_points,
                "max_points": COUNT_TIERS[0][1],
            }
        )

        score = min(score, MAX_SCORE)

        category = "unknown"

        for name, threshold in CATEGORY_THRESHOLDS:
            if score >= threshold:
                category = name
                break

        # Score 0 is "low" only if the report explicitly says there is no danger
        # signal. If nothing was stated, we cannot assess (unknown).
        if category == "unknown" and negative:
            category = "low"

        met = [
            f"{item['criterion']} (+{item['points']})"
            for item in criteria
            if item["points"] > 0
        ]

        if category == "unknown":
            summary = (
                "Urgency cannot be assessed: the report does not state any "
                "danger signals. This does not mean the situation is safe, "
                "only that information is missing."
            )
        else:
            summary = f"Urgency: {category} (score {score}/{MAX_SCORE})."

            if met:
                summary += " Contributing factors: " + "; ".join(met) + "."
            elif negative:
                summary += (
                    " The report explicitly states that the main danger "
                    "signals are absent."
                )

            if missing:
                summary += (
                    " Some information is missing, so the real urgency "
                    "may be higher."
                )

        explanation = (
            f"{summary} This is a rule-based estimate using only information "
            f"stated in the report (rules {RULES_VERSION}). It is not "
            "verified and requires human review."
        )

        key_phrases = source.get("key_phrases") or []
        evidence = [str(phrase) for phrase in key_phrases]

        return AgentResult(
            agent_name=self.name,
            output={
                "severity": category,
                "urgency_rank": URGENCY_RANK[category],
                "score": score,
                "max_score": MAX_SCORE,
                "criteria": criteria,
                "negative_evidence": negative,
                "category_thresholds": dict(CATEGORY_THRESHOLDS),
                "rules_version": RULES_VERSION,
            },
            explanation=explanation,
            supporting_evidence=evidence,
            missing_information=missing,
            requires_human_verification=True,
        )