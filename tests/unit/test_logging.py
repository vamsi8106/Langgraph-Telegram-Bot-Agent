import os, logging
from app.config.logging import configure_logging
from app.config.settings import settings

def test_write_log(tmp_path, monkeypatch):
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("APP_LOG_FILE", str(tmp_path / "logs/app.log"))
    configure_logging()
    logging.getLogger("app.test").info("hello")
    assert os.path.exists(settings.app_log_file)
