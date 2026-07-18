import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.database import database_is_connected, engine
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import CorrelationIdMiddleware
from app.core.security_middleware import SecureHeadersMiddleware
from app.core.observability import setup_observability
from app.schemas.common import RootResponse

settings = get_settings()
configure_logging(settings.log_level, settings.app_env)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    db_ok = database_is_connected()
    logger.info("Starting %s v%s (database=%s)", settings.app_name, settings.app_version, db_ok)
    
    if not db_ok and settings.app_env == "production":
        logger.error("Startup validation failed: Database connection could not be established in production.")
        raise RuntimeError("Startup validation failed: Database connection could not be established")
        
    yield
    
    logger.info("Stopping %s. Initiating graceful shutdown...", settings.app_name)
    engine.dispose()
    logger.info("Database connections closed.")


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
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(SecureHeadersMiddleware)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
register_exception_handlers(app)
setup_observability(app, settings.app_name, settings.app_env)


@app.get("/", response_model=RootResponse, tags=["root"])
def root() -> RootResponse:
    return RootResponse(
        name="CausalCast AI API",
        message="CausalCast AI backend is running",
        version=settings.app_version,
        docs="/docs",
        health="/health",
    )
