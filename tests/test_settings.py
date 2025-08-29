from src.infrastructure.settings import get_settings


def test_settings_defaults_and_structured_helpers():
    settings = get_settings()

    # Core defaults
    assert settings.app_name == "inteligencia_juridica"
    assert settings.stage == "dev"

    llm_cfg = settings.llm_config()
    assert llm_cfg["model"] == settings.llm_model

    meta = settings.meta()
    assert meta["app"] == settings.app_name
