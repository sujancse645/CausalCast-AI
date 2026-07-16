from fastapi import APIRouter

from app.api.routes import datasets, preparations, quality, schema_mapping, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(schema_mapping.router)
api_router.include_router(quality.router)
api_router.include_router(preparations.router)
api_router.include_router(datasets.router)
