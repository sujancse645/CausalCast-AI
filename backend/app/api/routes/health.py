from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.database import database_is_connected
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse | JSONResponse:
    connected = database_is_connected()
    response = HealthResponse(
        status="healthy" if connected else "degraded",
        service="causalcast-backend",
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(UTC),
    )
    if not connected:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=response.model_dump(mode="json"))
    return response

@router.get("/health/liveness", response_model=dict)
def liveness() -> dict:
    return {"status": "alive"}

@router.get("/health/readiness", response_model=dict)
def readiness() -> dict | JSONResponse:
    if database_is_connected():
        return {"status": "ready"}
    return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "not ready"})
