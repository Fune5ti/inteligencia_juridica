from __future__ import annotations

from functools import lru_cache
from typing import Dict, Any
from pydantic import BaseModel, Field

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

    model_config = {
        "extra": "ignore",  # Ignore unexpected vars
        "populate_by_name": True,
    }

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

    return Settings()  # type: ignore[arg-type]


__all__ = [
    "Settings",
    "get_settings",
    # Constant names (exported for discoverability / tests)
    "STAGE_ENV",
    "LLM_MODEL_ENV",
    "APP_NAME_ENV",
    "GEMINI_API_KEY_ENV",
    "GEMINI_MODEL_ENV",
]
