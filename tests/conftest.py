import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import app  # noqa: E402
from src.infrastructure.auth import require_api_key  # noqa: E402


@pytest.fixture(autouse=True)
def disable_auth():
    """Automatically disable API key auth in tests unless specifically testing it."""
    app.dependency_overrides[require_api_key] = lambda: "test-key"
    yield
    app.dependency_overrides.pop(require_api_key, None)


@pytest.fixture()
def client():
    return TestClient(app)
