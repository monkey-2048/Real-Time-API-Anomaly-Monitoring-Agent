from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EnvPulse"
    app_env: str = "dev"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite:///./envpulse.db"

    redis_url: str = "redis://redis:6379/0"
    redis_queue_name: str = "envpulse:observations"

    scheduler_interval_seconds: int = 60
    scheduler_timezone: str = "UTC"
    run_scheduler_in_api: bool = False

    default_latitude: float = 25.0330
    default_longitude: float = 121.5654
    default_location_name: str = "taipei"

    http_timeout_seconds: float = 8.0
    http_retry_attempts: int = 3

    anomaly_contamination: float = Field(default=0.03, ge=0.001, le=0.5)
    anomaly_min_samples: int = 40

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: float = 12.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
