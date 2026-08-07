"""Application configuration.

Every setting the app needs is declared here, read from environment variables
(or the .env file) once at startup, and shared everywhere else.

Nothing outside this file should ever read an environment variable directly.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The backend/ folder, worked out from this file's own location.
# config.py -> core/ -> app/ -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """All configuration values required to run the application."""

    # --- Application metadata ---
    APP_NAME: str = "AI Study Assistant"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Versioning the URL means we can ship a breaking /api/v2 later without
    # breaking clients that still call /api/v1.
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # SQLite for development. Swapped for a PostgreSQL URL in production
    # without changing a single line of application code.
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'study_assistant.db'}"

    @field_validator("DATABASE_URL")
    @classmethod
    def normalise_database_url(cls, value: str) -> str:
        """Rewrite the URL scheme hosting providers hand out.

        Render, Heroku and others set DATABASE_URL to `postgres://...`, which
        SQLAlchemy 2 does not recognise. It wants the dialect and driver named
        explicitly. Fixing it here means nobody has to remember at deploy time.
        """
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)

        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)

        return value

    # --- Frontend / CORS ---
    # Which origins the browser is allowed to call this API from. Comma
    # separated so it stays readable in a .env file.
    CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"

    # --- File uploads ---
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 10

    # --- Authentication ---
    # Signs every access token. Anyone who learns this value can forge a token
    # for any user, so it has no default and must come from the environment.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- AI ---
    # No default value: the app refuses to start if this is missing.
    GEMINI_API_KEY: str

    # Pinned on purpose. A "-latest" alias can change underneath us and
    # silently alter every answer the app gives.
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Rough guard on how much document text we send in one request. Protects
    # against both cost surprises and hitting the model's context limit.
    AI_MAX_INPUT_CHARS: int = 100_000

    # How many past chat messages to replay to the model. A sliding window:
    # enough for the conversation to feel continuous, capped so a long chat
    # cannot grow without limit.
    CHAT_HISTORY_LIMIT: int = 10

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


    @property
    def cors_origins_list(self) -> list[str]:
        """Split CORS_ORIGINS into the list the middleware expects."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Build the Settings object once and reuse it forever."""
    return Settings()


settings = get_settings()
