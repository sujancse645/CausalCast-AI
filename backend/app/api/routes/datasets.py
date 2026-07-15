from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import (
    DatasetNotFoundError,
    DatasetParseError,
    DatasetStorageError,
    DatasetTooLargeError,
    DuplicateDatasetError,
    InvalidDatasetError,
    UnsupportedDatasetTypeError,
)
from app.models.dataset import DatasetStatus
from app.schemas.dataset import (
    DatasetArchiveResponse,
    DatasetDetail,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetStatsResponse,
    DatasetUploadResponse,
)
from app.services.dataset_service import (
    archive_dataset,
    dataset_detail,
    dataset_preview,
    dataset_stats,
    list_datasets,
    upload_dataset,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload(file: Annotated[UploadFile, File()], db: Db, settings: Config) -> DatasetUploadResponse | JSONResponse:
    try:
        return await upload_dataset(file, db, settings)
    except DatasetTooLargeError as exc:
        return JSONResponse(status_code=413, content={"detail": str(exc)})
    except UnsupportedDatasetTypeError as exc:
        return JSONResponse(status_code=415, content={"detail": str(exc)})
    except DuplicateDatasetError as exc:
        return JSONResponse(status_code=409, content={"detail": str(exc), "existing_dataset_id": exc.dataset_id})
    except InvalidDatasetError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    except DatasetParseError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})
    except DatasetStorageError:
        return JSONResponse(status_code=500, content={"detail": "Dataset ingestion failed safely"})


@router.get("", response_model=DatasetListResponse)
def datasets(
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[DatasetStatus | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(max_length=200)] = None,
    sort: Annotated[Literal["newest", "oldest"], Query()] = "newest",
) -> DatasetListResponse:
    return list_datasets(db, page, page_size, status_filter, search, sort)


@router.get("/stats", response_model=DatasetStatsResponse)
def stats(db: Db) -> DatasetStatsResponse:
    return dataset_stats(db)


@router.get("/{dataset_id}", response_model=DatasetDetail)
def detail(dataset_id: str, db: Db) -> DatasetDetail | JSONResponse:
    try:
        return dataset_detail(db, dataset_id)
    except DatasetNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview(
    dataset_id: str, db: Db, settings: Config, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> DatasetPreviewResponse | JSONResponse:
    try:
        return dataset_preview(db, dataset_id, limit, settings.dataset_preview_rows)
    except DatasetNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


@router.delete("/{dataset_id}", response_model=DatasetArchiveResponse)
def archive(dataset_id: str, db: Db, settings: Config) -> DatasetArchiveResponse | JSONResponse:
    try:
        return archive_dataset(db, dataset_id, settings)
    except DatasetNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except DatasetStorageError:
        return JSONResponse(status_code=500, content={"detail": "Dataset could not be archived"})
