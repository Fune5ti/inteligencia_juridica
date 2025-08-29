from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import uuid
import requests
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
        now = datetime.now(timezone.utc)
        pdf_path = self._download_pdf(data.pdf_url, data.case_id)

        # For now we only record the download in timeline
        timeline = [
            {
                "stage": "download_pdf",
                "path": str(pdf_path),
                "timestamp": now.isoformat(),
            }
        ]
        resume = "PDF downloaded"
        return ExtractResponse(
            case_id=data.case_id,
            resume=resume,
            timeline=timeline,
            evidence=[],
            persisted_at=now,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _download_pdf(self, url: str, case_id: str) -> Path:
        """Download PDF to a temporary file.

        Returns path to the saved file. Raises RuntimeError on failure.
        """
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            if "pdf" not in resp.headers.get("Content-Type", "").lower():
                # Still save but note could refine later
                pass
            tmp_dir = Path(tempfile.gettempdir())
            filename = f"{case_id}_{uuid.uuid4().hex}.pdf"
            path = tmp_dir / filename
            path.write_bytes(resp.content)
            return path
        except Exception as exc:  # Broad catch; convert to domain-level error
            raise RuntimeError(f"Failed to download PDF: {exc}") from exc


def get_extract_service() -> ExtractService:  # Simple factory (could add DI later)
    return ExtractService()

__all__ = [
    "ExtractRequest",
    "ExtractResponse",
    "ExtractService",
    "get_extract_service",
]
