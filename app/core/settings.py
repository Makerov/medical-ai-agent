from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "medical-ai-agent"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    artifact_root_dir: Path = Path("data/artifacts")
    debug: bool = False
    log_level: str = "INFO"
    doctor_telegram_id_allowlist: Annotated[tuple[int, ...], NoDecode] = ()
    debug_admin_static_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("doctor_telegram_id_allowlist", mode="before")
    @classmethod
    def parse_doctor_telegram_id_allowlist(cls, value: object) -> tuple[int, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            raw_items = [item.strip() for item in value.split(",")]
            return tuple(int(item) for item in raw_items if item)
        if isinstance(value, int):
            return (value,)
        if isinstance(value, list | tuple | set):
            return tuple(int(item) for item in value)
        msg = "DOCTOR_TELEGRAM_ID_ALLOWLIST must be a comma-separated list of integers"
        raise ValueError(msg)

    @field_validator("debug_admin_static_token", mode="before")
    @classmethod
    def normalize_debug_admin_static_token(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        msg = "DEBUG_ADMIN_STATIC_TOKEN must be a string"
        raise ValueError(msg)

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

    @field_validator("artifact_root_dir", mode="before")
    @classmethod
    def validate_artifact_root_dir(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            msg = "ARTIFACT_ROOT_DIR must not be empty"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
