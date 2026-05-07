from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.schemas.runtime_health import (
    RuntimeLivenessResponse,
    RuntimeProcess,
    RuntimeReadinessResponse,
    StartupVerificationResponse,
)
from app.services.runtime_health_service import RuntimeHealthService


def get_runtime_health_service() -> RuntimeHealthService:
    return RuntimeHealthService()


router = APIRouter()


@router.get("/health", response_model=RuntimeLivenessResponse)
def health(
    runtime_health_service: Annotated[
        RuntimeHealthService,
        Depends(get_runtime_health_service),
    ],
    process: Annotated[RuntimeProcess, Query()] = RuntimeProcess.API,
) -> RuntimeLivenessResponse:
    return runtime_health_service.build_liveness(process=process)


@router.get("/health/readiness", response_model=RuntimeReadinessResponse)
def readiness(
    runtime_health_service: Annotated[
        RuntimeHealthService,
        Depends(get_runtime_health_service),
    ],
    process: Annotated[RuntimeProcess, Query()] = RuntimeProcess.API,
) -> RuntimeReadinessResponse:
    return runtime_health_service.evaluate_readiness(process=process)


@router.get("/health/startup", response_model=StartupVerificationResponse)
def startup(
    runtime_health_service: Annotated[
        RuntimeHealthService,
        Depends(get_runtime_health_service),
    ],
    process: Annotated[RuntimeProcess, Query()] = RuntimeProcess.API,
) -> StartupVerificationResponse:
    return runtime_health_service.verify_startup(process=process)
