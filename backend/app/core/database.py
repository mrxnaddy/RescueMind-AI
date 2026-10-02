from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def get_database_url() -> str:
    """Read DATABASE_URL from .env and make it use the psycopg driver."""
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is empty. Check the .env file in the project root.")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


# The engine is the connection to PostgreSQL.
engine = create_engine(get_database_url(), pool_pre_ping=True)

# A session is one conversation with the database (one request = one session).
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """FastAPI dependency: gives an endpoint a database session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()