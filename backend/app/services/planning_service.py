from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.agents.planning_agent import ResponsePlanningAgent
from app.agents.resource_agent import ResourceMatchingAgent
from app.models.incident_history import IncidentHistory
from app.models.response_plan import ResponsePlan
from app.orchestrator.orchestrator import Orchestrator


class PlanningError(Exception):
    """Raised when a plan could not be generated."""


def generate_plan(incident_id: int, db: Session) -> ResponsePlan:
    """Run Matching -> Planning and save the result as a proposed plan."""

    orchestrator = Orchestrator(
        [ResourceMatchingAgent(db), ResponsePlanningAgent(db)],
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
        raise PlanningError(
            f"Plan generation failed at {pipeline.failed_agent}: {error}"
        )

    plan_data = jsonable_encoder(
        pipeline.results["response_planning_agent"]["output"]
    )

    # Only one active proposal per incident.
    (
        db.query(ResponsePlan)
        .filter(
            ResponsePlan.incident_id == incident_id,
            ResponsePlan.status == "proposed",
        )
        .update({"status": "superseded"}, synchronize_session=False)
    )

    record = ResponsePlan(
        incident_id=incident_id,
        status="proposed",
        plan=plan_data,
    )
    db.add(record)
    db.flush()

    db.add(
        IncidentHistory(
            incident_id=incident_id,
            action="response_plan_proposed",
            new_value=f"plan #{record.id}",
            notes=(
                "A response plan was proposed. It needs human approval; no "
                "resource has been assigned."
            ),
        )
    )
    db.commit()
    db.refresh(record)

    return record