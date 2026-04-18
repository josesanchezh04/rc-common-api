"""Configuration settings for API Gateway."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel  
from functools import lru_cache

class ServicesSettings(BaseModel):
    auth_service_url: str
    user_service_url: str

class Settings(BaseSettings):
    """API Gateway configuration."""
    ms: ServicesSettings

    api_gateway_port: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()

