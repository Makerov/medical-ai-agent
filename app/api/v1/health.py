from fastapi import APIRouter
from pydantic import BaseModel

from app.core.settings import get_settings


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.environment,
    )
