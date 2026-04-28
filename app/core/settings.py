from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "medical-ai-agent"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("api_v1_prefix")
    @classmethod
    def validate_api_v1_prefix(cls, value: str) -> str:
        if not value:
            msg = "API_V1_PREFIX must not be empty"
            raise ValueError(msg)
        if not value.startswith("/"):
            msg = "API_V1_PREFIX must start with '/'"
            raise ValueError(msg)
        if value == "/":
            msg = "API_V1_PREFIX must not be '/'"
            raise ValueError(msg)
        if value != "/" and value.endswith("/"):
            return value.rstrip("/")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
