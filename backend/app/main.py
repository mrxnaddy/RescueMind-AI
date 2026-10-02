from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered property marketing and customer communication platform.",
)

app.include_router(health_router, prefix="/api")


@app.get("/", tags=["Root"])
def root():
    return {"message": f"Welcome to {settings.app_name}", "docs": "/docs"}