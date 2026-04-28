from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
