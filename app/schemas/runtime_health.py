from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RuntimeProcess(StrEnum):
    API = "api"
    PATIENT_BOT = "patient_bot"
    DOCTOR_BOT = "doctor_bot"
    WORKER = "worker"


class RuntimeDependencyStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


class RuntimeReadinessStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    NOT_READY = "not_ready"


class RuntimeLivenessResponse(BaseModel):
    process: RuntimeProcess = RuntimeProcess.API
    status: Literal["live"] = "live"
    service: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    runtime_profile: str = Field(min_length=1)


class RuntimeDependencyCheck(BaseModel):
    name: str = Field(min_length=1)
    required: bool
    status: RuntimeDependencyStatus
    reason_code: str | None = None
    detail: str | None = None


class RuntimeReadinessResponse(BaseModel):
    process: RuntimeProcess
    status: RuntimeReadinessStatus
    runtime_profile: str = Field(min_length=1)
    dependencies: tuple[RuntimeDependencyCheck, ...]
    reason_codes: tuple[str, ...] = ()
