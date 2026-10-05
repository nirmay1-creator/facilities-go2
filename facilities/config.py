"""
Application configuration loaded from environment variables / .env file.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    lm_studio_url: str = "http://localhost:1234/v1"
    model_name: str = "qwen3-vl-8b"
    request_timeout: int = 60
    max_tokens: int = 512
    database_path: str = "./data/facilities.db"
    provider_mode: str = "lmstudio"  # "lmstudio" | "mock"


settings = Settings()
