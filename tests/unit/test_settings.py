from app.config.settings import settings

def test_defaults():
    assert settings.env in {"dev", "prod", "test"}
    assert settings.app_log_file.endswith("app.log")
