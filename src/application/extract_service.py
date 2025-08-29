from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import uuid
import requests
from pydantic import BaseModel, HttpUrl, Field
from ..infrastructure.gemini_client import get_gemini_client, GeminiClient
from .extraction_models import CaseExtraction, Event, Evidence


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
    """

    async def extract(self, data: ExtractRequest) -> ExtractResponse:
        now = datetime.now(timezone.utc)
        pdf_path = self._download_pdf(data.pdf_url, data.case_id)
        timeline: list[dict] = [
            {
                "stage": "download_pdf",
                "path": str(pdf_path),
                "timestamp": now.isoformat(),
            }
        ]

        gemini_client = get_gemini_client()
        resume = "PDF downloaded"
        evidence: list[dict] = []

        if gemini_client:
            try:
                prompt = self._build_prompt()
                model_output = gemini_client.analyze_pdf(str(pdf_path), prompt)
                resume = model_output.get("resume", resume)
                timeline.append(
                    {
                        "stage": "gemini_analysis",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                if model_output.get("timeline"):
                    timeline.extend(model_output["timeline"]) 
                evidence = model_output.get("evidence", evidence)  
            except Exception as exc:  # pragma: no cover - best effort
                timeline.append(
                    {
                        "stage": "gemini_error",
                        "error": str(exc),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

        return ExtractResponse(
            case_id=data.case_id,
            resume=resume,
            timeline=timeline,
            evidence=evidence,
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

    def _build_prompt(self) -> str:
        return (
            "You are a legal document analyzer. Given the PDF, extract: \n"
            "1) A concise resume (summary).\n"
            "2) A timeline as a JSON array of objects with keys: event_id, event_name, event_description, "
            "event_date (ISO), event_page_init, event_page_end.\n"
            "3) An evidence list as JSON array of objects with keys: evidence_id, evidence_name, evidence_flaw, "
            "evidence_page_init, evidence_page_end.\n"
            "Respond strictly in JSON with top-level keys: resume, timeline, evidence."
        )


def get_extract_service() -> ExtractService:  # Simple factory (could add DI later)
    return ExtractService()

__all__ = [
    "ExtractRequest",
    "ExtractResponse",
    "ExtractService",
    "get_extract_service",
]
