from fastapi.testclient import TestClient
from unittest.mock import Mock
from pathlib import Path
import tempfile
from src.main import app
from src.infrastructure.pdf_downloader import get_pdf_downloader
from src.infrastructure.gemini_client import get_gemini_client


client = TestClient(app)


def test_post_extract_endpoint():
    payload = {
        "pdf_url": "https://example.com/processo.pdf",
        "case_id": "0809090-86.2024.8.12.0021",
    }
    # Mock downloader adapter
    tmp_pdf = Path(tempfile.gettempdir()) / "test.pdf"
    tmp_pdf.write_bytes(b"%PDF-1.4 test pdf")
    mock_downloader = Mock()
    mock_downloader.download.return_value = tmp_pdf

    app.dependency_overrides[get_pdf_downloader] = lambda: mock_downloader
    app.dependency_overrides[get_gemini_client] = lambda: None
    try:
        resp = client.post("/extract", json=payload)
    finally:
        app.dependency_overrides.pop(get_pdf_downloader, None)
        app.dependency_overrides.pop(get_gemini_client, None)
    assert resp.status_code == 200
    data = resp.json()
    # debug key may appear when debug mode auto-enabled; ensure at least required keys
    for k in ["resume", "timeline", "evidence"]:
        assert k in data
    # Resume should at least be a string; when no model it remains default
    assert isinstance(data["resume"], str)
    # Internal stages like 'download_pdf' removed; timeline may be empty without model output
    assert isinstance(data["timeline"], list)
    assert isinstance(data["evidence"], list)
