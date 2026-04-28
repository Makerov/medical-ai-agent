import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.settings import get_settings
from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_typed_smoke_response() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert isinstance(payload["service"], str)
    assert payload["service"]
    assert isinstance(payload["environment"], str)
    assert payload["environment"]


def test_openapi_schema_contains_health_route() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]


def test_settings_reject_invalid_api_prefix(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("API_V1_PREFIX", "api/v1")

    try:
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_reject_root_api_prefix(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("API_V1_PREFIX", "/")

    try:
        with pytest.raises(ValidationError):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_settings_parse_doctor_telegram_id_allowlist(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DOCTOR_TELEGRAM_ID_ALLOWLIST", "123, 456")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.doctor_telegram_id_allowlist == (123, 456)


def test_settings_normalize_debug_admin_static_token(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DEBUG_ADMIN_STATIC_TOKEN", " demo-token ")

    try:
        settings = get_settings()
    finally:
        get_settings.cache_clear()

    assert settings.debug_admin_static_token == "demo-token"
