from typing import Annotated

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.settings import get_settings
from app.schemas.auth import AuthorizationError, CallerContext, CallerRole, Capability
from app.services.access_control_service import authorize_capability


class DoctorAccessSmokeResponse(BaseModel):
    status: str
    caller_role: CallerRole
    capability: Capability


router = APIRouter(prefix="/doctor")


@router.get("/protected-smoke", response_model=DoctorAccessSmokeResponse)
def protected_smoke(
    caller_role: Annotated[str | None, Header(alias="X-Caller-Role")] = None,
    telegram_user_id: Annotated[str | None, Header(alias="X-Telegram-User-Id")] = None,
    debug_admin_token: Annotated[str | None, Header(alias="X-Debug-Admin-Token")] = None,
) -> DoctorAccessSmokeResponse | JSONResponse:
    required_capability = Capability.DOCTOR_CASE_READ
    try:
        caller = _build_caller_context(caller_role, telegram_user_id, required_capability)
        settings = get_settings()
        authorize_capability(
            caller,
            required_capability,
            doctor_telegram_id_allowlist=settings.doctor_telegram_id_allowlist,
            debug_admin_token=debug_admin_token,
            configured_debug_admin_token=settings.debug_admin_static_token,
        )
    except AuthorizationError as error:
        return JSONResponse(status_code=403, content={"error": error.to_public_error()})

    return DoctorAccessSmokeResponse(
        status="ok",
        caller_role=caller.role,
        capability=required_capability,
    )


def _build_caller_context(
    role_value: str | None,
    telegram_user_id: str | None,
    required_capability: Capability,
) -> CallerContext:
    if role_value is None:
        raise AuthorizationError(
            code="caller_role_required",
            required_capability=required_capability,
            caller_role=None,
        )
    try:
        role = CallerRole(role_value)
    except ValueError as exc:
        raise AuthorizationError(
            code="unknown_caller_role",
            required_capability=required_capability,
            caller_role=None,
        ) from exc
    parsed_telegram_user_id = _parse_telegram_user_id(telegram_user_id, role, required_capability)
    return CallerContext(role=role, telegram_user_id=parsed_telegram_user_id)


def _parse_telegram_user_id(
    telegram_user_id: str | None,
    role: CallerRole,
    required_capability: Capability,
) -> int | None:
    if telegram_user_id is None:
        return None
    try:
        return int(telegram_user_id)
    except ValueError as exc:
        raise AuthorizationError(
            code="invalid_telegram_user_id",
            required_capability=required_capability,
            caller_role=role,
        ) from exc
