from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.routes import (
    auth,
    business_intelligence,
    datasets,
    deep_forecasting,
    deep_training,
    explainability,
    forecasting,
    preparations,
    production_forecast,
    quality,
    rag,
    schema_mapping,
    system,
)

api_router = APIRouter()
api_router.include_router(auth.router)

# Protected routes
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(system.router)
protected_router.include_router(schema_mapping.router)
protected_router.include_router(quality.router)
protected_router.include_router(preparations.router)
protected_router.include_router(forecasting.router)
protected_router.include_router(deep_forecasting.router)
protected_router.include_router(deep_training.router)
protected_router.include_router(datasets.router)
protected_router.include_router(explainability.router)
protected_router.include_router(business_intelligence.router)
protected_router.include_router(rag.router)
protected_router.include_router(production_forecast.router)

api_router.include_router(protected_router)
