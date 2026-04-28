from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class CallerRole(StrEnum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    DEBUG_ADMIN = "debug_admin"


class Capability(StrEnum):
    PATIENT_CASE_READ = "patient_case_read"
    PATIENT_INTAKE_WRITE = "patient_intake_write"
    DOCTOR_CASE_READ = "doctor_case_read"
    DOCTOR_READY_CASE_LIST = "doctor_ready_case_list"
    DEBUG_ADMIN_ACCESS = "debug_admin_access"


class CallerContext(BaseModel):
    role: CallerRole
    telegram_user_id: int | None = None

    model_config = ConfigDict(frozen=True)


class AuthorizationError(Exception):
    def __init__(
        self,
        *,
        code: str,
        required_capability: Capability,
        caller_role: CallerRole | None,
        message: str = "Access denied for this capability.",
    ) -> None:
        self.code = code
        self.required_capability = required_capability
        self.caller_role = caller_role
        self.public_message = message
        super().__init__(code)

    def to_public_error(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "required_capability": self.required_capability.value,
            "caller_role": self.caller_role.value if self.caller_role else None,
            "message": self.public_message,
        }
