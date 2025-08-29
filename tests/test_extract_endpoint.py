from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from src.main import app


client = TestClient(app)


def test_post_extract_endpoint():
    payload = {
        "pdf_url": "https://example.com/processo.pdf",
        "case_id": "0809090-86.2024.8.12.0021",
    }
    fake_content = b"%PDF-1.4 test pdf"
    mock_resp = Mock()
    mock_resp.content = fake_content
    mock_resp.headers = {"Content-Type": "application/pdf"}
    mock_resp.raise_for_status = Mock()

    with patch("src.application.extract_service.requests.get", return_value=mock_resp), patch(
        "src.application.extract_service.get_gemini_client", return_value=None
    ):
        resp = client.post("/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"resume", "timeline", "evidence"}
    assert data["resume"] == "PDF downloaded"
    assert isinstance(data["timeline"], list) and data["timeline"][0]["stage"] == "download_pdf"
    assert isinstance(data["evidence"], list)
