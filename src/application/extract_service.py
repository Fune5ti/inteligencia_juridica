from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import uuid
import requests
from pydantic import BaseModel, HttpUrl, Field
from ..infrastructure.gemini_client import get_gemini_client, GeminiClient
from ..infrastructure.pdf_downloader import get_pdf_downloader, RequestsPdfDownloader
from .extraction_models import CaseExtraction, Event, Evidence


class ExtractRequest(BaseModel):
    pdf_url: HttpUrl
    case_id: str = Field(min_length=5)


class ExtractResponse(BaseModel):
    resume: str
    timeline: list[Event]
    evidence: list[Evidence]
    # Optional debug diagnostics (only populated when debug flag enabled)
    debug: dict | None = None


class ExtractService:
    """Service responsible for orchestrating extraction pipeline.

    Dependencies are injected (pdf_downloader, gemini_client provider) to honor layered architecture.
    """

    def __init__(self, pdf_downloader: RequestsPdfDownloader, gemini_client: GeminiClient | None):
        self._pdf_downloader = pdf_downloader
        self._gemini_client = gemini_client

    async def extract(self, data: ExtractRequest, *, debug: bool | None = None) -> ExtractResponse:
        pdf_path = self._pdf_downloader.download(str(data.pdf_url), data.case_id)
        timeline: list[Event] = []
        gemini_client = self._gemini_client
        resume = "PDF downloaded"
        evidence: list[Evidence] = []
        debug_enabled = debug

        if debug_enabled is None:
            import os
            debug_enabled = os.getenv("INTJ_DEBUG", "0") in {"1", "true", "TRUE", "yes", "on"}
        debug_payload: dict | None = {"prompt": None} if debug_enabled else None

        if gemini_client:
            try:
                prompt = self._build_prompt()
                if debug_payload is not None:
                    debug_payload["prompt"] = prompt
                model_output = gemini_client.analyze_pdf(str(pdf_path), prompt)
                resume = model_output.get("resume", resume)
                if model_output.get("timeline"):
                    for ev in model_output["timeline"]:
                        try:
                            timeline.append(Event(**ev))
                        except Exception:
                            continue
                raw_evidence = model_output.get("evidence", [])
                evidence = []
                for evd in raw_evidence:
                    try:
                        evidence.append(Evidence(**evd))
                    except Exception:
                        continue
                if debug_payload is not None:
                    if "validation_error" in model_output:
                        debug_payload["validation_error"] = model_output["validation_error"]
                    debug_payload["timeline_count"] = len(model_output.get("timeline", []))
                    debug_payload["evidence_count"] = len(model_output.get("evidence", []))
            except Exception as exc:  # pragma: no cover
                timeline.append(
                    {
                        "stage": "gemini_error",
                        "error": str(exc),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                if debug_payload is not None:
                    debug_payload["error"] = str(exc)

        return ExtractResponse(
            resume=resume,
            timeline=timeline,
            evidence=evidence,
            debug=debug_payload,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    # _download_pdf removed in favor of infrastructure adapter

    def _build_prompt(self) -> str:
        # Multilingual + strict JSON output instructions. Provide both EN and PT to reduce ambiguity.
        schema = self._schema_example()
        return (
            "ROLE: You are an expert legal document analyst (analista jurídico especializado).\n\n"
            "TASK (EN): Read the supplied PDF document and extract ONLY the requested structured data.\n"
            "TAREFA (PT-BR): Leia o PDF fornecido e extraia APENAS os dados estruturados solicitados.\n\n"
            "OUTPUT RULES / REGRAS DE SAÍDA:\n"
            "1. Return ONE single JSON object.\n"
            "2. Do NOT include explanations, commentary, markdown, code fences, or additional keys.\n"
            "3. Keys required at top level: resume, timeline, evidence.\n"
            "4. resume: concise case summary in Portuguese (máx ~120 palavras).\n"
            "5. timeline: array of chronological events. Each event has: event_id (int, sequential from 0), "
            "event_name (short label PT-BR), event_description (objective PT-BR), event_date (DD/MM/YYYY if present; else ISO or empty string), "
            "event_page_init (int), event_page_end (int).\n"
            "6. evidence: array of evidences with: evidence_id (int sequential from 0), evidence_name, evidence_flaw (describe irregularidade ou 'Sem inconsistências'), evidence_page_init, evidence_page_end.\n"
            "7. If any field unknown, use empty string (''), but keep the key.\n"
            "8. event_id and evidence_id MUST be strictly incremental starting at 0 with no gaps.\n"
            "9. PAGE numbers must be integers derived from the PDF order (first page = 1).\n"
            "10. DO NOT hallucinate dates; if absent, set event_date to ''.\n"
            "11. No duplicate events; merge if redundant.\n"
            "12. Output must be valid JSON parseable by a standard JSON parser.\n"
            "13. Do NOT wrap JSON in backticks.\n\n"
            "JSON SCHEMA EXAMPLE (MODEL ONLY – ADAPT CONTENT):\n" + schema + "\n"
            "BEGIN NOW. Return ONLY the JSON object."
        )

    def _schema_example(self) -> str:
        return (
            '{"resume": "Resumo conciso do caso...", "timeline": ['
            '{"event_id":0, "event_name":"Marco Inicial", "event_description":"Ajuizamento da ação...", '
            '"event_date":"22/10/2024", "event_page_init":1, "event_page_end":13}, '
            '{"event_id":1, "event_name":"Decisão Interlocutória", "event_description":"Tutela concedida...", '
            '"event_date":"23/10/2024", "event_page_init":32, "event_page_end":34}'
            '], "evidence": ['
            '{"evidence_id":0, "evidence_name":"Procuração", "evidence_flaw":"Sem inconsistências", "evidence_page_init":16, "evidence_page_end":16}, '
            '{"evidence_id":1, "evidence_name":"Contrato", "evidence_flaw":"Assinatura ilegível", "evidence_page_init":20, "evidence_page_end":21}'
            ']}'
        )


def get_extract_service(
    pdf_downloader: RequestsPdfDownloader | None = None,
    gemini_client: GeminiClient | None = None,
) -> ExtractService:
    return ExtractService(
        pdf_downloader=pdf_downloader or get_pdf_downloader(),
        gemini_client=gemini_client if gemini_client is not None else get_gemini_client(),
    )

__all__ = [
    "ExtractRequest",
    "ExtractResponse",
    "ExtractService",
    "get_extract_service",
]
