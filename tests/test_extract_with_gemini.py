from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_extract_endpoint_with_gemini_analysis():
    payload = {
        "pdf_url": "https://example.com/file.pdf",
        "case_id": "12345-00.2024.8.00.0000",
    }

    # Mock PDF download
    mock_pdf_resp = Mock()
    mock_pdf_resp.content = b"%PDF-1.4 test pdf"
    mock_pdf_resp.headers = {"Content-Type": "application/pdf"}
    mock_pdf_resp.raise_for_status = Mock()

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

    with patch("src.application.extract_service.requests.get", return_value=mock_pdf_resp), patch(
        "src.application.extract_service.get_gemini_client", return_value=mock_gemini_client
    ):
        resp = client.post("/extract", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["resume"] == "Sample resume"
    # timeline should include download + gemini_analysis + model provided event
    stages = [t.get("stage") for t in data["timeline"]]
    assert "download_pdf" in stages
    assert "gemini_analysis" in stages
    # Evidence list forwarded
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["evidence_id"] == 10