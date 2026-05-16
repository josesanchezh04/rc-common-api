"""Configuration settings for API Gateway."""
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServicesSettings(BaseModel):
    """Downstream microservice URLs."""

    auth_service_url: str
    user_service_url: str


class Settings(BaseSettings):
    """API Gateway configuration."""

    env: Literal["development", "staging", "production"] = "development"
    ms: ServicesSettings
    api_gateway_port: int = 4000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings instance.

    Returns:
        Singleton Settings object loaded from environment / .env file.
    """
    return Settings()


