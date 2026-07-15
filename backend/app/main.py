import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.database import database_is_connected
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.schemas.common import RootResponse

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s v%s (database=%s)", settings.app_name, settings.app_version, database_is_connected())
    yield
    logger.info("Stopping %s", settings.app_name)


app = FastAPI(
    title="CausalCast AI API",
    description="Backend API for probabilistic revenue forecasting and marketing decision intelligence",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)
app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
register_exception_handlers(app)


@app.get("/", response_model=RootResponse, tags=["root"])
def root() -> RootResponse:
    return RootResponse(
        name="CausalCast AI API",
        message="CausalCast AI backend is running",
        version=settings.app_version,
        docs="/docs",
        health="/health",
    )
