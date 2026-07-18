from fastapi import APIRouter

from app.api.routes import (
    datasets,
    deep_forecasting,
    deep_training,
    forecasting,
    preparations,
    quality,
    schema_mapping,
    system,
    explainability,
)

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(schema_mapping.router)
api_router.include_router(quality.router)
api_router.include_router(preparations.router)
api_router.include_router(forecasting.router)
api_router.include_router(deep_forecasting.router)
api_router.include_router(deep_training.router)
api_router.include_router(datasets.router)
api_router.include_router(explainability.router)
