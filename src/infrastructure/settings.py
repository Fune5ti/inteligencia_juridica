from __future__ import annotations

from functools import lru_cache
from typing import Dict, Any
from pydantic import BaseModel, Field
import os

try:  
    from dotenv import load_dotenv

    load_dotenv()
except Exception: 
    pass


# ---------------------------------------------------------------------------
# Environment variable name constants 
# ---------------------------------------------------------------------------
STAGE_ENV = "STAGE"
LLM_MODEL_ENV = "LLM_MODEL"
APP_NAME_ENV = "APP_NAME"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_MODEL_ENV = "GEMINI_MODEL"
DB_HOST_ENV = "POSTGRES_HOST"
DB_PORT_ENV = "POSTGRES_PORT"
DB_USER_ENV = "POSTGRES_USER"
DB_PASSWORD_ENV = "POSTGRES_PASSWORD"
DB_NAME_ENV = "POSTGRES_DB"


class Settings(BaseModel):
    """Application settings loaded from environment variables.

    Provide typed fields with safe defaults for local development.
    """

    # Core
    app_name: str = Field(default="inteligencia_juridica", validation_alias=APP_NAME_ENV)
    stage: str = Field(default="dev", validation_alias=STAGE_ENV)

    # Integrations
    llm_model: str = Field(default="dummy-model", validation_alias=LLM_MODEL_ENV)
    gemini_api_key: str | None = Field(default=None, validation_alias=GEMINI_API_KEY_ENV)
    gemini_model: str = Field(default="gemini-1.5-flash", validation_alias=GEMINI_MODEL_ENV)
    # Database
    db_host: str = Field(default="localhost", validation_alias=DB_HOST_ENV)
    db_port: int = Field(default=5432, validation_alias=DB_PORT_ENV)
    db_user: str = Field(default="postgres", validation_alias=DB_USER_ENV)
    db_password: str = Field(default="postgres", validation_alias=DB_PASSWORD_ENV)
    db_name: str = Field(default="inteligencia_juridica", validation_alias=DB_NAME_ENV)

    model_config = {"extra": "ignore", "populate_by_name": True}

    # ------------------------------------------------------------------
    # Structured config helpers
    # ------------------------------------------------------------------

    def llm_config(self) -> Dict[str, str]:
        return {
            "model": self.llm_model,
            "stage": self.stage,
        }

    def gemini_config(self) -> Dict[str, Any]:
        return {
            "model": self.gemini_model,
            "has_key": bool(self.gemini_api_key),
        }

    def database_url(self) -> str:
        # Prefer modern psycopg (v3); fall back to psycopg2 if only that is installed
        driver = "psycopg"
        try:  # pragma: no cover - import check
            import psycopg  # type: ignore  # noqa: F401
        except Exception:  # pragma: no cover
            driver = "psycopg2"
        return f"postgresql+{driver}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    def meta(self) -> Dict[str, str]:  # General metadata aggregator
        return {
            "app": self.app_name,
            "stage": self.stage,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached Settings factory.

    lru_cache ensures we only parse environment once per process.
    """

    return Settings(
        app_name=os.getenv(APP_NAME_ENV, "inteligencia_juridica"),
        stage=os.getenv(STAGE_ENV, "dev"),
        llm_model=os.getenv(LLM_MODEL_ENV, "dummy-model"),
        gemini_api_key=os.getenv(GEMINI_API_KEY_ENV),
        gemini_model=os.getenv(GEMINI_MODEL_ENV, "gemini-1.5-flash"),
    db_host=os.getenv(DB_HOST_ENV, "localhost"),
    db_port=int(os.getenv(DB_PORT_ENV, "5432")),
    db_user=os.getenv(DB_USER_ENV, "postgres"),
    db_password=os.getenv(DB_PASSWORD_ENV, "postgres"),
    db_name=os.getenv(DB_NAME_ENV, "inteligencia_juridica"),
    )


__all__ = [
    "Settings",
    "get_settings",
    # Constant names (exported for discoverability / tests)
    "STAGE_ENV",
    "LLM_MODEL_ENV",
    "APP_NAME_ENV",
    "GEMINI_API_KEY_ENV",
    "GEMINI_MODEL_ENV",
    "DB_HOST_ENV",
    "DB_PORT_ENV",
    "DB_USER_ENV",
    "DB_PASSWORD_ENV",
    "DB_NAME_ENV",
]
