from unittest.mock import patch, Mock
from src.infrastructure.gemini_client import GeminiClient


def test_gemini_client_validates_case_extraction_success():
    client = GeminiClient(api_key="dummy", model="gemini-1.5-flash")

    fake_raw = '{"resume": "r", "timeline": [{"event_id": 1, "event_name": "n", "event_description": "d", "event_date": "2024-01-01", "event_page_init": 1, "event_page_end": 2}], "evidence": [{"evidence_id": 10, "evidence_name": "Contract", "evidence_flaw": "None", "evidence_page_init": 3, "evidence_page_end": 4}]}'

    mock_file = Mock(uri="file://abc", mime_type="application/pdf", name="file123", state=Mock(name="COMPLETED"))
    mock_model = Mock()
    mock_model.generate_content.return_value = Mock(text=fake_raw)

    fake_genai = Mock()
    fake_genai.upload_file.return_value = mock_file
    fake_genai.get_file.return_value = mock_file
    fake_genai.GenerativeModel.return_value = mock_model
    with patch("src.infrastructure.gemini_client.genai", new=fake_genai):
        out = client.analyze_pdf("/tmp/x.pdf", "prompt")

    assert out["resume"] == "r"
    assert len(out["timeline"]) == 1
    assert len(out["evidence"]) == 1
    assert "validation_error" not in out


def test_gemini_client_validation_fallback_on_bad_json():
    client = GeminiClient(api_key="dummy", model="gemini-1.5-flash")
    # Malformed JSON (missing evidence array structure)
    fake_raw = '{"resume": "r", "timeline": [], "evidence": {"bad": 1}}'

    mock_file = Mock(uri="file://abc", mime_type="application/pdf", name="file123", state=Mock(name="COMPLETED"))
    mock_model = Mock()
    mock_model.generate_content.return_value = Mock(text=fake_raw)

    fake_genai = Mock()
    fake_genai.upload_file.return_value = mock_file
    fake_genai.get_file.return_value = mock_file
    fake_genai.GenerativeModel.return_value = mock_model
    with patch("src.infrastructure.gemini_client.genai", new=fake_genai):
        out = client.analyze_pdf("/tmp/x.pdf", "prompt")

    assert out["resume"] == "r"
    assert out.get("validation_error") is True