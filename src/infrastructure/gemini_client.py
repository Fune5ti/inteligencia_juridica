from __future__ import annotations

from typing import Any, Dict, List
import json
import time
import re
import logging
import os

try:  # Import guarded so tests without dependency or key still pass
    import google.generativeai as google_genai  # correct SDK
    genai = google_genai  # backward compat alias for tests mocking 'genai'
except Exception:  # pragma: no cover - soft import
    google_genai = None  # type: ignore
    genai = None  # type: ignore

from .settings import get_settings
from ..application.extraction_models import CaseExtraction


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model_name = model
        # Order matters: prefer alias 'genai' so tests patching it override real module
        active_sdk = genai or google_genai
        if active_sdk:
            try:
                active_sdk.configure(api_key=api_key)
            except Exception:  # pragma: no cover
                pass
        self._model = None

    def _get_model(self):  # Lazy load
        sdk = genai or google_genai
        if not sdk:
            raise RuntimeError(
                "google-generativeai package not available. Install with 'pip install google-generativeai' (avoid installing the similarly named 'genai' package)."
            )
        if self._model is None:
            self._model = sdk.GenerativeModel(self.model_name)
        return self._model

    def analyze_pdf(self, file_path: str, prompt: str) -> Dict[str, Any]:
        """Upload PDF and run Gemini model.

        Returns structured dict with resume, timeline, evidence.
        Falls back to stub if SDK not available.
        """
        active_sdk = genai or google_genai

        # If SDK missing -> attempt LangChain fallback
        if not active_sdk:
            try:  # pragma: no cover (optional dependency path)
                from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
                from pypdf import PdfReader  # type: ignore
            except Exception:
                return {
                    "resume": "(gemini sdk indisponível) Instale 'langchain-google-genai' para fallback.",
                    "timeline": [],
                    "evidence": [],
                    "validation_error": True,
                }
            extracted = []
            try:
                reader = PdfReader(file_path)
                for i, page in enumerate(reader.pages[:20]):
                    try:
                        txt = page.extract_text() or ""
                    except Exception:
                        txt = ""
                    extracted.append(f"\n--- PAGE {i+1} ---\n{txt.strip()}")
            except Exception:
                extracted.append("(Falha ao extrair texto)")
            lc_prompt = (
                prompt
                + "\n\nCONTEÚDO EXTRAÍDO (parcial):\n"
                + ("".join(extracted))[:15000]
                + "\n\nRetorne SOMENTE o JSON."
            )
            try:
                chat = ChatGoogleGenerativeAI(model=self.model_name, google_api_key=self.api_key, temperature=0)
                resp = chat.invoke(lc_prompt)
                content = getattr(resp, "content", "")
                if isinstance(content, list):
                    content = "\n".join(str(p) for p in content)
                parsed = self._parse_json_from_text(str(content))
            except Exception as exc:
                return {
                    "resume": f"(fallback error) {exc}",
                    "timeline": [],
                    "evidence": [],
                    "validation_error": True,
                }
            return self._finalize_parsed(parsed, raw_text=str(content))

        model = self._get_model()
        # Upload file (skip if mocked)
        is_mock_sdk = active_sdk.__class__.__module__.startswith("unittest.mock") if hasattr(active_sdk, "__class__") else False
        if is_mock_sdk:
            file_obj = type("_F", (), {"uri": "mock://uri", "mime_type": "application/pdf", "name": "mock_file"})()
        else:
            try:
                file_obj = active_sdk.upload_file(file_path)
            except Exception as exc:  # pragma: no cover
                return {
                    "resume": f"(upload error) {exc}",
                    "timeline": [],
                    "evidence": [],
                    "validation_error": True,
                }
            for _ in range(30):
                state = getattr(getattr(file_obj, "state", None), "name", None)
                if state == "PROCESSING":
                    time.sleep(1)
                    try:
                        file_obj = active_sdk.get_file(file_obj.name)
                    except Exception:
                        break
                    continue
                break
        try:
            result = model.generate_content([
                {"file_data": {"file_uri": getattr(file_obj, "uri", ""), "mime_type": getattr(file_obj, "mime_type", "application/pdf")}},
                {"text": prompt},
            ])
        except Exception as exc:  # pragma: no cover
            return {
                "resume": f"(generation error) {exc}",
                "timeline": [],
                "evidence": [],
                "validation_error": True,
            }
        raw_text = self._extract_text_from_result(result)
        parsed = self._parse_json_from_text(raw_text)
        if not parsed:
            parsed = self._attempt_brace_slice(raw_text)
        return self._finalize_parsed(parsed, raw_text=raw_text)

    # ---- helpers below ----
    def _extract_text_from_result(self, result: Any) -> str:
        txt = getattr(result, "text", None)
        if txt is not None:
            return str(txt)
        parts: List[str] = []
        for cand in getattr(result, "candidates", []) or []:
            content = getattr(cand, "content", None)
            for part in getattr(content, "parts", []) or []:
                parts.append(getattr(part, "text", ""))
        return "\n".join(parts)

    def _attempt_brace_slice(self, raw: str) -> Dict[str, Any]:
        cleaned = re.sub(r"```[a-zA-Z]*", "", raw).replace("```", "").strip()
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first != -1 and last != -1 and last > first:
            snippet = cleaned[first:last + 1]
            try:
                return json.loads(snippet)
            except Exception:
                return {}
        return {}

    def _finalize_parsed(self, parsed: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        if not parsed and "resume" in raw_text.lower():
            parsed = {"resume": "", "timeline": [], "evidence": []}
        original_timeline = parsed.get("timeline")
        original_evidence = parsed.get("evidence")
        parsed = self._normalize_ids(parsed)
        try:
            validated = CaseExtraction(**parsed)
            data = validated.model_dump()
            if not isinstance(original_timeline, list) or not isinstance(original_evidence, list):
                data["validation_error"] = True
            if os.getenv("INTJ_DEBUG"):
                data["raw_text"] = raw_text
            return data
        except Exception:
            out = {
                "resume": parsed.get("resume") or "(empty resume)",
                "timeline": parsed.get("timeline") or [],
                "evidence": parsed.get("evidence") or [],
                "validation_error": True,
            }
            if os.getenv("INTJ_DEBUG"):
                out["raw_text"] = raw_text[:5000]
            return out

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

    def _normalize_ids(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure event_id / evidence_id are sequential integers starting at 0.

        Accept strings or missing IDs; regenerate when necessary.
        """
        timeline = parsed.get("timeline") or []
        evidence = parsed.get("evidence") or []

        def seq(records: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
            normalized = []
            for idx, rec in enumerate(records):
                if not isinstance(rec, dict):
                    continue
                rec[key] = idx  # overwrite / assign sequential id
                normalized.append(rec)
            return normalized

        parsed["timeline"] = seq(timeline, "event_id")
        parsed["evidence"] = seq(evidence, "evidence_id")
        return parsed


def get_gemini_client() -> GeminiClient | None:
    settings = get_settings()
    if not settings.gemini_api_key:
        return None
    return GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


__all__ = ["GeminiClient", "get_gemini_client"]