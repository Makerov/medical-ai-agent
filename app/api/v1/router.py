from fastapi import APIRouter

from app.api.v1.doctor import router as doctor_router
from app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(doctor_router, tags=["doctor"])
