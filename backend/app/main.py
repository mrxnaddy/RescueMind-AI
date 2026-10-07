from fastapi import FastAPI
from sqlalchemy import text
from app.database import Base, engine
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
from app.routes.emergency_reports import router as emergency_reports_router
from app.routes.agents import router as agents_router
from app.routes.orchestrator import router as orchestrator_router
from app.routes.analysis import router as analysis_router
from app.routes.incidents import router as incidents_router
from app.routes.duplicates import router as duplicates_router
from app.routes.resources import router as resources_router
from app.routes.matching import router as matching_router
from app.routes.plans import router as plans_router
from app.routes.assignments import router as assignments_router
from app.routes.incident_status import router as incident_status_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.map import router as map_router
from app.routes.agent_executions import router as agent_executions_router
from app.routes import incident_history
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine


app = FastAPI(
    title="RescueMind AI",
    description="AI-powered Emergency Intelligence Platform",
    version="1.0.0",
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://rescue-mind-a63xee6zu-agentx3.vercel.app",  # Apna actual Vercel domain yahan likhein
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(emergency_reports_router)
app.include_router(agents_router)
app.include_router(orchestrator_router)
app.include_router(analysis_router)
app.include_router(incidents_router)
app.include_router(duplicates_router)
app.include_router(resources_router)
app.include_router(matching_router)
app.include_router(plans_router)
app.include_router(assignments_router)
app.include_router(incident_status_router)
app.include_router(map_router)
app.include_router(agent_executions_router)
app.include_router(incident_history.router)

Base.metadata.create_all(bind=engine)


@app.get("/")
def home():
    return {
        "message": "RescueMind AI Backend is running!",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "RescueMind AI",
    }


@app.get("/health/database")
def database_health_check():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "mysql_test": value,
    }
