from collections.abc import Container

from app.schemas.auth import AuthorizationError, CallerContext, CallerRole, Capability

_ROLE_CAPABILITIES: dict[CallerRole, frozenset[Capability]] = {
    CallerRole.PATIENT: frozenset(
        {
            Capability.PATIENT_CASE_READ,
            Capability.PATIENT_INTAKE_WRITE,
        }
    ),
    CallerRole.DOCTOR: frozenset(
        {
            Capability.DOCTOR_CASE_READ,
            Capability.DOCTOR_READY_CASE_LIST,
        }
    ),
    CallerRole.DEBUG_ADMIN: frozenset(Capability),
}

_DOCTOR_CAPABILITIES = frozenset(
    {
        Capability.DOCTOR_CASE_READ,
        Capability.DOCTOR_READY_CASE_LIST,
    }
)


def authorize_capability(
    caller: CallerContext,
    required_capability: Capability,
    *,
    doctor_telegram_id_allowlist: Container[int],
    debug_admin_token: str | None = None,
    configured_debug_admin_token: str | None = None,
) -> None:
    allowed_capabilities = _ROLE_CAPABILITIES[caller.role]
    if required_capability not in allowed_capabilities:
        raise AuthorizationError(
            code="forbidden",
            required_capability=required_capability,
            caller_role=caller.role,
        )

    if caller.role == CallerRole.DOCTOR and required_capability in _DOCTOR_CAPABILITIES:
        _authorize_allowlisted_doctor(caller, required_capability, doctor_telegram_id_allowlist)
    if caller.role == CallerRole.DEBUG_ADMIN:
        _authorize_debug_admin(
            caller,
            required_capability,
            debug_admin_token,
            configured_debug_admin_token,
        )


def _authorize_allowlisted_doctor(
    caller: CallerContext,
    required_capability: Capability,
    doctor_telegram_id_allowlist: Container[int],
) -> None:
    if caller.telegram_user_id is None:
        raise AuthorizationError(
            code="doctor_identity_required",
            required_capability=required_capability,
            caller_role=caller.role,
        )
    if caller.telegram_user_id not in doctor_telegram_id_allowlist:
        raise AuthorizationError(
            code="doctor_not_allowlisted",
            required_capability=required_capability,
            caller_role=caller.role,
        )


def _authorize_debug_admin(
    caller: CallerContext,
    required_capability: Capability,
    debug_admin_token: str | None,
    configured_debug_admin_token: str | None,
) -> None:
    if configured_debug_admin_token is None:
        raise AuthorizationError(
            code="debug_admin_not_configured",
            required_capability=required_capability,
            caller_role=caller.role,
        )
    if debug_admin_token is None:
        raise AuthorizationError(
            code="debug_admin_token_required",
            required_capability=required_capability,
            caller_role=caller.role,
        )
    if debug_admin_token != configured_debug_admin_token:
        raise AuthorizationError(
            code="debug_admin_token_invalid",
            required_capability=required_capability,
            caller_role=caller.role,
        )
