import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


def _is_reachable(url: str, default_port: int) -> bool:
    """Return True if something is listening at the host/port in this URL."""
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or default_port
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


@router.get("/health")
def health_check():
    """Simple check that the API itself is running."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "messaging_mode": settings.messaging_mode,  # "mock" = no real messages sent
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/services")
def services_health():
    """Check that PostgreSQL and Redis are reachable."""
    postgres_ok = _is_reachable(settings.database_url, 5432)
    redis_ok = _is_reachable(settings.redis_url, 6379)
    return {
        "status": "ok" if (postgres_ok and redis_ok) else "degraded",
        "postgres": "reachable" if postgres_ok else "unreachable",
        "redis": "reachable" if redis_ok else "unreachable",
    }