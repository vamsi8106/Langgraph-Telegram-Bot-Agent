
# src/app/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    env: Literal["dev", "prod", "test"] = "dev"
    debug: bool = True

    data_dir: str = "data"
    persist_dir: str = "long_term_memory"
    logs_dir: str = "logs"
    app_log_file: str = "logs/app.log"

    openai_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-large"
    openai_image_model: str = "gpt-image-1"

    elevenlabs_voice_id: str = "T8lgQl6x5PSdhmmWx42m"
    elevenlabs_model_id: str = "eleven_flash_v2_5"

    OPENAI_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    TELEGRAM_BOT_TOKEN: str | None = None

    enable_tracing: bool = False
    otlp_endpoint: str | None = None        # e.g., "http://otel-collector:4318"
    service_name: str = "karan-bot"

    enable_prometheus: bool = False
    prometheus_port: int = 9000             # /metrics will be served here
    metrics_namespace: str = "karan_bot"

    enable_json_logs: bool = False

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl_seconds: int = 86400
    window_size: int = 30

    # Postgres
    database_url: str = "postgresql+psycopg://karan1:karan1@localhost:5432/karandb1"

    # -------- NEW: Redis cache “folder” --------
    # Use a separate Redis DB index for cache (optional but clean):
    redis_cache_db: int = 1
    # Namespace acts like a folder path: all QA cache keys = cache:qa:<hash>
    qa_cache_namespace: str = "cache:qa"
    qa_cache_enabled: bool = True
    qa_cache_ttl_seconds: int = 6 * 3600
    qa_cache_min_chars: int = 8
    qa_cache_include_system_prompt: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()



