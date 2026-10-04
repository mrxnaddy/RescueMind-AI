from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "RescueMind AI"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 2
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.65
    DUPLICATE_HIGH_SIMILARITY: float = 0.78
    DUPLICATE_MAX_DISTANCE_KM: float = 2.0
    DUPLICATE_TIME_WINDOW_HOURS: int = 48
    RESOURCE_SEARCH_RADIUS_KM: float = 30.0

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()