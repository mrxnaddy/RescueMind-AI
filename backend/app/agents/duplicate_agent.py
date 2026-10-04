from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.config import settings
from app.models.incident import Incident
from app.models.incident_embedding import IncidentEmbedding
from app.models.incident_location import IncidentLocation
from app.schemas.agent import AgentResult
from app.services.embedding_service import (
    cosine_similarity,
    embed_text,
    get_model_name,
)
from app.utils.geo import haversine_km

MAX_CANDIDATES = 5
IGNORED_STATUSES = ["resolved", "merged"]


def build_embedding_text(incident: Incident) -> str:
    """Text used for the embedding: type + English summary + location.

    The Intake Agent already turned the report into an English summary,
    so reports written in Urdu or Roman Urdu can still be compared.
    """

    results = (incident.ai_analysis or {}).get("results") or {}
    intake = (results.get("intake_agent") or {}).get("output") or {}
    location = (results.get("location_agent") or {}).get("output") or {}

    label = incident.emergency_type.replace("_", " ")
    body = intake.get("summary") or incident.description or ""
    text = f"{label}. {body}".strip()

    place = location.get("normalized_address") or ", ".join(
        location.get("location_mentions") or []
    )

    if place:
        text += f" Location: {place}."

    return text


class DuplicateDetectionAgent(BaseAgent):
    """Finds potential duplicate incidents (embeddings + cosine similarity).

    It only suggests. A human must confirm before anything is merged.
    The agent saves the incident's own embedding so it can be compared
    with future incidents.
    """

    name = "duplicate_agent"

    def __init__(self, db: Session) -> None:
        self.db = db

    def _save_embedding(
        self,
        incident_id: int,
        text: str,
        vector: list[float],
    ) -> None:
        row = (
            self.db.query(IncidentEmbedding)
            .filter(IncidentEmbedding.incident_id == incident_id)
            .first()
        )

        if row is None:
            self.db.add(
                IncidentEmbedding(
                    incident_id=incident_id,
                    model_name=get_model_name(),
                    source_text=text,
                    embedding=vector,
                )
            )
        else:
            row.model_name = get_model_name()
            row.source_text = text
            row.embedding = vector

        self.db.commit()

    def _first_locations(
        self,
        incident_ids: list[int],
    ) -> dict[int, IncidentLocation]:
        rows = (
            self.db.query(IncidentLocation)
            .filter(IncidentLocation.incident_id.in_(incident_ids))
            .order_by(IncidentLocation.id)
            .all()
        )

        result: dict[int, IncidentLocation] = {}

        for row in rows:
            result.setdefault(row.incident_id, row)

        return result

    def process(self, input_data: dict[str, Any]) -> AgentResult:
        incident_id = input_data.get("incident_id")

        incident = (
            self.db.query(Incident)
            .filter(Incident.id == incident_id)
            .first()
        )

        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        text = build_embedding_text(incident)
        vector = embed_text(text)
        self._save_embedding(incident.id, text, vector)

        window = timedelta(hours=settings.DUPLICATE_TIME_WINDOW_HOURS)

        rows = (
            self.db.query(Incident, IncidentEmbedding)
            .join(
                IncidentEmbedding,
                IncidentEmbedding.incident_id == Incident.id,
            )
            .filter(Incident.id != incident.id)
            .filter(Incident.status.notin_(IGNORED_STATUSES))
            .filter(Incident.created_at >= incident.created_at - window)
            .filter(Incident.created_at <= incident.created_at + window)
            .all()
        )

        locations = self._first_locations(
            [incident.id] + [other.id for other, _ in rows]
        )
        my_location = locations.get(incident.id)

        threshold = settings.DUPLICATE_SIMILARITY_THRESHOLD
        candidates: list[dict[str, Any]] = []
        excluded_far = 0
        skipped_other_model = 0

        for other, embedding_row in rows:
            if embedding_row.model_name != get_model_name():
                skipped_other_model += 1
                continue

            similarity = cosine_similarity(vector, embedding_row.embedding)

            if similarity < threshold:
                continue

            other_location = locations.get(other.id)
            distance_km = None

            if my_location and other_location:
                distance_km = haversine_km(
                    my_location.latitude,
                    my_location.longitude,
                    other_location.latitude,
                    other_location.longitude,
                )

            if (
                distance_km is not None
                and distance_km > settings.DUPLICATE_MAX_DISTANCE_KM
            ):
                excluded_far += 1
                continue

            same_type = other.emergency_type == incident.emergency_type
            hours_apart = (
                abs((other.created_at - incident.created_at).total_seconds())
                / 3600
            )

            warnings: list[str] = []

            if not same_type:
                warnings.append(
                    "Different emergency type selected "
                    f"({other.emergency_type} vs {incident.emergency_type})"
                )

            if distance_km is None:
                warnings.append(
                    "Distance could not be checked because coordinates are "
                    "not available for both incidents"
                )

            candidates.append(
                {
                    "candidate_incident_id": other.id,
                    "incident_code": other.incident_code,
                    "title": other.title,
                    "similarity": round(similarity, 4),
                    "strength": (
                        "high"
                        if similarity >= settings.DUPLICATE_HIGH_SIMILARITY
                        else "medium"
                    ),
                    "same_emergency_type": same_type,
                    "distance_km": (
                        None if distance_km is None else round(distance_km, 2)
                    ),
                    "hours_apart": round(hours_apart, 2),
                    "warnings": warnings,
                }
            )

        candidates.sort(key=lambda item: item["similarity"], reverse=True)
        candidates = candidates[:MAX_CANDIDATES]

        compared = len(rows) - skipped_other_model

        if candidates:
            best = candidates[0]
            explanation = (
                f"Found {len(candidates)} potential duplicate(s) among "
                f"{compared} compared incident(s). Most similar: "
                f"{best['incident_code']} (similarity {best['similarity']}). "
                "These are suggestions only: a human must confirm before any "
                "merge, and the original reports are always preserved."
            )
        else:
            explanation = (
                f"No potential duplicates found among {compared} compared "
                f"incident(s) (similarity threshold {threshold}). This does "
                "not guarantee the incident is new; it only means no similar "
                "incident was found in the comparison window."
            )

        if excluded_far:
            explanation += (
                f" {excluded_far} similar incident(s) were excluded because "
                f"they are more than {settings.DUPLICATE_MAX_DISTANCE_KM} km "
                "away."
            )

        evidence: list[str] = []

        for item in candidates:
            distance_text = (
                "distance unknown"
                if item["distance_km"] is None
                else f"{item['distance_km']} km apart"
            )
            evidence.append(
                f"{item['incident_code']}: similarity {item['similarity']}, "
                f"{distance_text}, {item['hours_apart']} h apart"
            )

        missing: list[str] = []

        if my_location is None:
            missing.append(
                "Distance check skipped: this incident has no coordinates"
            )

        return AgentResult(
            agent_name=self.name,
            output={
                "candidates": candidates,
                "compared_with": compared,
                "excluded_due_to_distance": excluded_far,
                "skipped_other_embedding_model": skipped_other_model,
                "threshold": threshold,
                "embedding_model": get_model_name(),
                "text_used": text,
            },
            explanation=explanation,
            supporting_evidence=evidence,
            missing_information=missing,
            requires_human_verification=True,
        )