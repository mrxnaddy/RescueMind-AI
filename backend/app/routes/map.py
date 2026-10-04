from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.models.incident_location import IncidentLocation


router = APIRouter(
    prefix="/api/map",
    tags=["Emergency Map"],
)


@router.get("/incidents")
def get_map_incidents(
    db: Session = Depends(get_db),
):
    incidents = (
        db.query(Incident)
        .filter(Incident.status != "merged")
        .order_by(Incident.created_at.desc())
        .all()
    )

    result = []

    for incident in incidents:
        location = (
            db.query(IncidentLocation)
            .filter(
                IncidentLocation.incident_id == incident.id
            )
            .order_by(IncidentLocation.id.desc())
            .first()
        )

        if location is None:
            continue

        result.append(
            {
                "id": incident.id,
                "incident_code": incident.incident_code,
                "title": incident.title,
                "emergency_type": incident.emergency_type,
                "severity": incident.severity,
                "status": incident.status,
                "report_count": incident.report_count,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "address": location.address,
                "location_source": location.location_source,
                "created_at": incident.created_at,
                "updated_at": incident.updated_at,
            }
        )

    return {
        "count": len(result),
        "incidents": result,
        "note": (
            "Map data is based on simulated incident information. "
            "AI-derived assessments are not verified emergency facts."
        ),
    }