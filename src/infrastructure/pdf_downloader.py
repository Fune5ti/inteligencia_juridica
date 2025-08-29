from __future__ import annotations

from pathlib import Path
import tempfile
import uuid
import requests
from typing import Optional

from ..domain.repositories import PdfDownloader

class RequestsPdfDownloader(PdfDownloader):
    """Downloads PDFs using requests.

    Keeps pure IO details out of application services.
    """

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def download(self, url: str, case_id: str) -> Path:
        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            # Not strictly validating content-type; could enforce 'application/pdf'
            tmp_dir = Path(tempfile.gettempdir())
            filename = f"{case_id}_{uuid.uuid4().hex}.pdf"
            path = tmp_dir / filename
            path.write_bytes(resp.content)
            return path
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Failed to download PDF: {exc}") from exc


_downloader_singleton: Optional[RequestsPdfDownloader] = None

def get_pdf_downloader() -> RequestsPdfDownloader:
    global _downloader_singleton
    if _downloader_singleton is None:
        _downloader_singleton = RequestsPdfDownloader()
    return _downloader_singleton

__all__ = ["RequestsPdfDownloader", "get_pdf_downloader"]
