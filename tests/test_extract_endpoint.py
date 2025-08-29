from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_post_extract_endpoint():
    payload = {
        "pdf_url": "https://example.com/processo.pdf",
        "case_id": "0809090-86.2024.8.12.0021",
    }
    resp = client.post("/extract", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == payload["case_id"]
    assert "resume" in data
    assert isinstance(data["timeline"], list)
    assert isinstance(data["evidence"], list)
    assert "persisted_at" in data
