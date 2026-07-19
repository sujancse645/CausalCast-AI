from collections.abc import Callable
from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.preparation import (
    FeatureCatalogResponse,
    PreparationCreateRequest,
    PreparationHistoryResponse,
    PreparationPreviewResponse,
    PreparationResponse,
    PreparationSplitResponse,
    PreparationStatsResponse,
)
from app.services.preparation_service import (
    PreparationError,
    create_preparation,
    get_features,
    get_preparation,
    get_preview,
    get_splits,
    get_stats,
    list_preparations,
)
from app.services.preparation_storage_service import PreparationStorageService

router = APIRouter(tags=["preparations"])
T = TypeVar("T")
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


def _safe(call: Callable[[], T]) -> T:
    try:
        return call()
    except PreparationError as exc:
        import logging

        logging.getLogger("app").exception(exc)
        message = str(exc)
        raise HTTPException(status_code=404 if "not found" in message else 409, detail=message) from exc


@router.post("/datasets/{dataset_id}/preparations", response_model=PreparationResponse, status_code=201)
def create(
    dataset_id: UUID,
    request: PreparationCreateRequest,
    db: Db,
    settings: Config,
) -> PreparationResponse:
    return _safe(lambda: create_preparation(db, str(dataset_id), request.config, settings))


@router.get("/datasets/{dataset_id}/preparations", response_model=PreparationHistoryResponse)
def history(dataset_id: UUID, db: Db) -> PreparationHistoryResponse:
    return list_preparations(db, str(dataset_id))


@router.get("/preparations/stats", response_model=PreparationStatsResponse)
def stats(db: Db) -> PreparationStatsResponse:
    return get_stats(db)


@router.get("/preparations/{prepared_id}", response_model=PreparationResponse)
def detail(prepared_id: UUID, db: Db) -> PreparationResponse:
    return _safe(lambda: get_preparation(db, str(prepared_id)))


@router.get("/preparations/{prepared_id}/preview", response_model=PreparationPreviewResponse)
def preview(prepared_id: UUID, db: Db, settings: Config) -> PreparationPreviewResponse:
    return _safe(lambda: get_preview(db, str(prepared_id), settings))


@router.get("/preparations/{prepared_id}/features", response_model=FeatureCatalogResponse)
def features(prepared_id: UUID, db: Db) -> FeatureCatalogResponse:
    return _safe(lambda: get_features(db, str(prepared_id)))


@router.get("/preparations/{prepared_id}/splits", response_model=PreparationSplitResponse)
def splits(prepared_id: UUID, db: Db, settings: Config) -> PreparationSplitResponse:
    return _safe(lambda: get_splits(db, str(prepared_id), settings))


@router.get("/preparations/{prepared_id}/download", response_class=FileResponse)
def download(
    prepared_id: UUID,
    db: Db,
    settings: Config,
    artifact_format: Annotated[str, Query(alias="format", pattern="^csv$")] = "csv",
) -> FileResponse:
    item = _safe(lambda: get_preparation(db, str(prepared_id)))
    try:
        path = PreparationStorageService(settings).artifact(str(prepared_id))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Prepared artifact is unavailable") from exc
    return FileResponse(path, media_type="text/csv", filename=f"causalcast-prepared-{item.id}.{artifact_format}")
