from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl, Field


class ExtractRequest(BaseModel):
    pdf_url: HttpUrl
    case_id: str = Field(min_length=5)


class ExtractResponse(BaseModel):
    case_id: str
    resume: str
    timeline: list[dict]  # Placeholder structure; refine later
    evidence: list[dict]  # Placeholder structure; refine later
    persisted_at: datetime


class ExtractService:
    """Service responsible for orchestrating extraction pipeline.

    Currently a stub – in future this would download the PDF, run OCR / LLM, etc.
    """

    async def extract(self, data: ExtractRequest) -> ExtractResponse:
        # Placeholder implementation returning stubbed structure
        now = datetime.now(timezone.utc)
        return ExtractResponse(
            case_id=data.case_id,
            resume="Extraction initialized",
            timeline=[],
            evidence=[],
            persisted_at=now,
        )


def get_extract_service() -> ExtractService:  # Simple factory (could add DI later)
    return ExtractService()

__all__ = [
    "ExtractRequest",
    "ExtractResponse",
    "ExtractService",
    "get_extract_service",
]
