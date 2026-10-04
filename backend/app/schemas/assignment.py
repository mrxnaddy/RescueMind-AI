from datetime import datetime

from pydantic import BaseModel


class AssignmentView(BaseModel):
    id: int
    incident_id: int
    incident_code: str
    resource_id: int
    resource_name: str
    resource_type: str
    quantity: int
    status: str
    assigned_at: datetime | None = None
    created_at: datetime