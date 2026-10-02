from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root folder (where .env lives): config.py -> core -> app -> backend -> root
ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and the .env file."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore .env values we don't use yet
    )

    app_name: str = "Naddy Property Dealer AI Agent"
    app_env: str = "development"
    secret_key: str = "change-me"
    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    messaging_mode: str = "mock"


settings = Settings()