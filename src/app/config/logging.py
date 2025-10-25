# src/app/config/logging.py
import logging
import logging.handlers
import os
from .settings import settings

def configure_logging():
    os.makedirs(settings.logs_dir, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    if settings.enable_json_logs:
        fmt = '{"ts":"%(asctime)s","lvl":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'
        ch.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%dT%H:%M:%S%z"))
    else:
        ch.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))

    fh = logging.handlers.RotatingFileHandler(
        settings.app_log_file, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(ch.formatter)

    root.handlers.clear()
    root.addHandler(ch)
    root.addHandler(fh)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.INFO)
