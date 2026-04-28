import pytest

from app.schemas.auth import AuthorizationError, CallerContext, CallerRole, Capability
from app.services.access_control_service import authorize_capability


def test_patient_cannot_access_doctor_capability() -> None:
    caller = CallerContext(role=CallerRole.PATIENT, telegram_user_id=101)

    with pytest.raises(AuthorizationError) as exc_info:
        authorize_capability(
            caller,
            Capability.DOCTOR_CASE_READ,
            doctor_telegram_id_allowlist={101},
        )

    error = exc_info.value
    assert error.code == "forbidden"
    assert error.required_capability == Capability.DOCTOR_CASE_READ
    assert error.caller_role == CallerRole.PATIENT
    assert error.to_public_error() == {
        "code": "forbidden",
        "required_capability": "doctor_case_read",
        "caller_role": "patient",
        "message": "Access denied for this capability.",
    }


def test_doctor_capability_requires_allowlisted_telegram_id() -> None:
    caller = CallerContext(role=CallerRole.DOCTOR, telegram_user_id=999)

    with pytest.raises(AuthorizationError) as exc_info:
        authorize_capability(
            caller,
            Capability.DOCTOR_CASE_READ,
            doctor_telegram_id_allowlist={123},
        )

    assert exc_info.value.to_public_error()["code"] == "doctor_not_allowlisted"


def test_doctor_can_access_doctor_capability_when_allowlisted() -> None:
    caller = CallerContext(role=CallerRole.DOCTOR, telegram_user_id=123)

    authorize_capability(
        caller,
        Capability.DOCTOR_CASE_READ,
        doctor_telegram_id_allowlist={123},
    )


def test_debug_admin_can_access_doctor_and_debug_capabilities_without_doctor_allowlist() -> None:
    caller = CallerContext(role=CallerRole.DEBUG_ADMIN)

    authorize_capability(
        caller,
        Capability.DOCTOR_CASE_READ,
        doctor_telegram_id_allowlist=set(),
        debug_admin_token="demo-token",
        configured_debug_admin_token="demo-token",
    )
    authorize_capability(
        caller,
        Capability.DEBUG_ADMIN_ACCESS,
        doctor_telegram_id_allowlist=set(),
        debug_admin_token="demo-token",
        configured_debug_admin_token="demo-token",
    )


def test_doctor_cannot_write_patient_intake() -> None:
    caller = CallerContext(role=CallerRole.DOCTOR, telegram_user_id=123)

    with pytest.raises(AuthorizationError):
        authorize_capability(
            caller,
            Capability.PATIENT_INTAKE_WRITE,
            doctor_telegram_id_allowlist={123},
        )


def test_missing_doctor_identity_is_structured_denial() -> None:
    caller = CallerContext(role=CallerRole.DOCTOR)

    with pytest.raises(AuthorizationError) as exc_info:
        authorize_capability(
            caller,
            Capability.DOCTOR_READY_CASE_LIST,
            doctor_telegram_id_allowlist={123},
        )

    error = exc_info.value.to_public_error()
    assert error["code"] == "doctor_identity_required"
    assert error["caller_role"] == "doctor"


def test_debug_admin_requires_static_token() -> None:
    caller = CallerContext(role=CallerRole.DEBUG_ADMIN)

    with pytest.raises(AuthorizationError) as exc_info:
        authorize_capability(
            caller,
            Capability.DEBUG_ADMIN_ACCESS,
            doctor_telegram_id_allowlist=set(),
            configured_debug_admin_token="demo-token",
        )

    error = exc_info.value.to_public_error()
    assert error["code"] == "debug_admin_token_required"
    assert error["caller_role"] == "debug_admin"
