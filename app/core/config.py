from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:///./mykare.db"
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    livekit_url: str | None = None
    livekit_api_key: str | None = None
    livekit_api_secret: str | None = None
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    deepgram_api_key: str | None = None
    cartesia_api_key: str | None = None
    default_timezone: str = "Asia/Kolkata"
    business_day_start_hour: int = Field(default=10, ge=0, le=23)
    business_day_end_hour: int = Field(default=17, ge=1, le=23)
    appointment_slot_interval_minutes: int = Field(default=30, ge=5, le=120)
    session_token_ttl_minutes: int = Field(default=60, ge=5, le=1440)

    @property
    def is_dev(self) -> bool:
        return self.app_env in {"development", "test"}

    def require_provider(self, value: str | None, provider_name: str) -> str:
        if value:
            return value
        if self.is_dev:
            return ""
        raise ValueError(f"{provider_name} credentials are required in {self.app_env} mode.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
