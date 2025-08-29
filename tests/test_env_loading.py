import os
from pathlib import Path
from src.infrastructure.settings import Settings


def test_env_file_loading(tmp_path, monkeypatch):
    monkeypatch.setenv("STAGE", "prod")
    monkeypatch.setenv("APP_NAME", "custom_app")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-custom")
    from importlib import reload
    import src.infrastructure.settings as settings_module
    reload(settings_module)  # Reset cached get_settings
    settings_module.get_settings.cache_clear()  # type: ignore[attr-defined]
    settings = settings_module.get_settings()
    assert settings.stage == "prod"
    assert settings.app_name == "custom_app"
    assert settings.gemini_model == "gemini-custom"