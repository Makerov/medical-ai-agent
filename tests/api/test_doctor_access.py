from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app


def test_allowlisted_doctor_can_access_protected_smoke_endpoint(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DOCTOR_TELEGRAM_ID_ALLOWLIST", "123,456")

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/doctor/protected-smoke",
            headers={"X-Caller-Role": "doctor", "X-Telegram-User-Id": "123"},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "caller_role": "doctor",
        "capability": "doctor_case_read",
    }


def test_patient_gets_structured_forbidden_without_internal_details() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/doctor/protected-smoke",
        headers={"X-Caller-Role": "patient", "X-Telegram-User-Id": "321"},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload == {
        "error": {
            "code": "forbidden",
            "required_capability": "doctor_case_read",
            "caller_role": "patient",
            "message": "Access denied for this capability.",
        }
    }
    assert "traceback" not in str(payload).lower()
    assert "AuthorizationError" not in str(payload)
    assert "app.services" not in str(payload)


def test_unallowlisted_doctor_gets_structured_forbidden(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DOCTOR_TELEGRAM_ID_ALLOWLIST", "123")

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/doctor/protected-smoke",
            headers={"X-Caller-Role": "doctor", "X-Telegram-User-Id": "999"},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 403
    payload = response.json()
    assert payload["error"]["code"] == "doctor_not_allowlisted"
    assert payload["error"]["required_capability"] == "doctor_case_read"
    assert payload["error"]["caller_role"] == "doctor"
    assert "traceback" not in str(payload).lower()


def test_invalid_telegram_user_id_gets_structured_forbidden() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/doctor/protected-smoke",
        headers={"X-Caller-Role": "doctor", "X-Telegram-User-Id": "abc"},
    )

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "invalid_telegram_user_id",
        "required_capability": "doctor_case_read",
        "caller_role": "doctor",
        "message": "Access denied for this capability.",
    }


def test_missing_role_gets_structured_forbidden() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/doctor/protected-smoke")

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "caller_role_required",
        "required_capability": "doctor_case_read",
        "caller_role": None,
        "message": "Access denied for this capability.",
    }


def test_debug_admin_requires_static_token(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DEBUG_ADMIN_STATIC_TOKEN", "demo-token")

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/doctor/protected-smoke",
            headers={"X-Caller-Role": "debug_admin"},
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "debug_admin_token_required",
        "required_capability": "doctor_case_read",
        "caller_role": "debug_admin",
        "message": "Access denied for this capability.",
    }


def test_debug_admin_with_valid_static_token_can_access_protected_smoke_endpoint(
    monkeypatch,
) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("DEBUG_ADMIN_STATIC_TOKEN", "demo-token")

    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/doctor/protected-smoke",
            headers={
                "X-Caller-Role": "debug_admin",
                "X-Debug-Admin-Token": "demo-token",
            },
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "caller_role": "debug_admin",
        "capability": "doctor_case_read",
    }


def test_health_endpoint_remains_public() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
