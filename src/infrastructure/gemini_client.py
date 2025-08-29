from __future__ import annotations

from typing import Any, Dict
import json
import time
import re

try:  # Import guarded so tests without dependency or key still pass
    import google.generativeai as genai
except Exception:  # pragma: no cover - soft import
    genai = None  # type: ignore

from .settings import get_settings
from ..application.extraction_models import CaseExtraction


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model_name = model
        if genai:
            genai.configure(api_key=api_key)
        self._model = None

    def _get_model(self):  # Lazy load
        if not genai:
            raise RuntimeError("google-generativeai package not available")
        if self._model is None:
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def analyze_pdf(self, file_path: str, prompt: str) -> Dict[str, Any]:
        """Upload PDF and run Gemini model.

        Returns structured dict with resume, timeline, evidence.
        Falls back to stub if SDK not available.
        """
        if not genai:
            return {
                "resume": "(gemini sdk unavailable) stub resume",
                "timeline": [],
                "evidence": [],
            }

        model = self._get_model()

        file_obj = genai.upload_file(file_path)
        for _ in range(30):
            file_state = getattr(file_obj, "state", None)
            name = getattr(file_state, "name", None)
            if name == "PROCESSING":
                time.sleep(1)
                file_obj = genai.get_file(file_obj.name)
                continue
            break

        result = model.generate_content([
            {"file_data": {"file_uri": file_obj.uri, "mime_type": getattr(file_obj, "mime_type", "application/pdf")}},
            {"text": prompt},
        ])
        raw_text = getattr(result, "text", None)
        if raw_text is None:
            parts = []
            for cand in getattr(result, "candidates", []) or []:
                for part in getattr(getattr(cand, "content", None), "parts", []) or []:
                    parts.append(getattr(part, "text", ""))
            raw_text = "\n".join(parts)

        parsed = self._parse_json_from_text(raw_text)
        try:
            validated = CaseExtraction(**parsed)
            return {
                "resume": validated.resume,
                "timeline": [e.model_dump() for e in validated.timeline],
                "evidence": [e.model_dump() for e in validated.evidence],
                "raw_model_output": raw_text,
            }
        except Exception:
            # Return fallback with raw output for debugging
            return {
                "resume": parsed.get("resume") or "(empty resume)",
                "timeline": parsed.get("timeline") or [],
                "evidence": parsed.get("evidence") or [],
                "raw_model_output": raw_text,
                "validation_error": True,
            }

    def _parse_json_from_text(self, text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except Exception:
            pass
        match = re.search(r"\{[\s\S]*\}\s*$", text.strip())
        if match:
            snippet = match.group(0)
            try:
                return json.loads(snippet)
            except Exception:
                return {}
        return {}


def get_gemini_client() -> GeminiClient | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    return GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


__all__ = ["GeminiClient", "get_gemini_client"]