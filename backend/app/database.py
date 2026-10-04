from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

from app.models.user import User  
from app.models.emergency_report import EmergencyReport  
from app.models.incident import Incident    
from app.models.incident_location import IncidentLocation
from app.models.incident_evidence import IncidentEvidence
from app.models.resource import Resource
from app.models.resource_assignment import ResourceAssignment
from app.models.agent_execution import AgentExecution
from app.models.incident_history import IncidentHistory
from app.models.audit_log import AuditLog