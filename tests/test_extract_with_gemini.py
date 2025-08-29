from unittest.mock import Mock
from pathlib import Path
import tempfile
from fastapi.testclient import TestClient
from src.main import app
from src.infrastructure.pdf_downloader import get_pdf_downloader
from src.infrastructure.gemini_client import get_gemini_client

client = TestClient(app)


def test_extract_endpoint_with_gemini_analysis():
    payload = {
        "pdf_url": "https://example.com/file.pdf",
        "case_id": "12345-00.2024.8.00.0000",
    }

    # Mock PDF downloader adapter
    tmp_pdf = Path(tempfile.gettempdir()) / "test2.pdf"
    tmp_pdf.write_bytes(b"%PDF-1.4 test pdf")
    mock_downloader = Mock()
    mock_downloader.download.return_value = tmp_pdf

    fake_model_output = {
        "resume": "Sample resume",
        "timeline": [
            {
                "event_id": 1,
                "event_name": "Petition",
                "event_description": "Initial petition filed",
                "event_date": "2024-01-01",
                "event_page_init": 1,
                "event_page_end": 2,
            }
        ],
        "evidence": [
            {
                "evidence_id": 10,
                "evidence_name": "Contract",
                "evidence_flaw": "Illegible signature",
                "evidence_page_init": 10,
                "evidence_page_end": 12,
            }
        ],
    }

    mock_gemini_client = Mock()
    mock_gemini_client.analyze_pdf.return_value = fake_model_output

    app.dependency_overrides[get_pdf_downloader] = lambda: mock_downloader
    app.dependency_overrides[get_gemini_client] = lambda: mock_gemini_client
    try:
        resp = client.post("/extract", json=payload)
    finally:
        app.dependency_overrides.pop(get_pdf_downloader, None)
        app.dependency_overrides.pop(get_gemini_client, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["resume"] == "Sample resume"
    # timeline now only includes model-provided events (no internal pipeline stages)
    stages = [t.get("stage") for t in data["timeline"] if isinstance(t, dict)]
    # Evidence list forwarded
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["evidence_id"] == 10