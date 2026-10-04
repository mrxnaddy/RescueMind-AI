from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.resource_agent import (
    DEFAULT_RELIEF_KITS,
    REQUIREMENT_RULES,
    RULES_VERSION,
    ResourceMatchingAgent,
)
from app.config import settings
from app.database import get_db
from app.models.incident import Incident
from app.orchestrator.orchestrator import Orchestrator
from app.schemas.agent import AgentResult

router = APIRouter(
    prefix="/api/matching",
    tags=["Resource Matching"],
)


@router.get("/rules")
def get_matching_rules():
    """The predefined, transparent rules the agent uses."""

    return {
        "rules_version": RULES_VERSION,
        "requirements_by_emergency_type": REQUIREMENT_RULES,
        "default_relief_kits": DEFAULT_RELIEF_KITS,
        "search_radius_km": settings.RESOURCE_SEARCH_RADIUS_KM,
        "note": (
            "Quantities of rules marked scale_critical increase by 1 when "
            "the incident severity is critical."
        ),
    }


@router.post(
    "/incidents/{incident_id}/recommend",
    response_model=AgentResult,
)
def recommend_resources(
    incident_id: int,
    db: Session = Depends(get_db),
):
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    orchestrator = Orchestrator(
        [ResourceMatchingAgent(db)],
        max_retries=1,
    )

    pipeline = orchestrator.run(
        {"incident_id": incident_id},
        db,
        incident_id=incident_id,
    )

    if pipeline.status != "completed":
        failed_step = pipeline.steps[-1] if pipeline.steps else None
        error = failed_step.error if failed_step else "unknown error"
        raise HTTPException(
            status_code=502,
            detail=f"Resource matching failed: {error}",
        )

    return AgentResult(**pipeline.results["resource_matching_agent"])