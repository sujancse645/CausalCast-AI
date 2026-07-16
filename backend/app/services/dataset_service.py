import logging
from datetime import UTC, datetime
from time import monotonic

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    DatasetNotFoundError,
    DatasetStorageError,
    DuplicateDatasetError,
    InvalidDatasetError,
    UnsupportedDatasetTypeError,
)
from app.models.dataset import Dataset, DatasetStatus
from app.models.preparation import PreparationStatus, PreparedDataset
from app.models.quality import DatasetQualityReport, QualityReportStatus
from app.models.schema_profile import DatasetSchemaProfile, SchemaStatus
from app.schemas.dataset import (
    DatasetArchiveResponse,
    DatasetDetail,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetStatsResponse,
    DatasetSummary,
    DatasetUploadResponse,
    DatasetWarning,
    PaginationMetadata,
)
from app.services.dataset_parser_service import parse_csv
from app.services.dataset_storage_service import DatasetStorageService

logger = logging.getLogger(__name__)


def _extension(filename: str | None) -> str:
    normalized = DatasetStorageService.normalize_filename(filename)
    parts = normalized.lower().split(".")
    if len(parts) != 2 or not parts[0]:
        raise UnsupportedDatasetTypeError("Only a single .csv extension is allowed")
    return parts[-1]


def _detail(dataset: Dataset) -> DatasetDetail:
    warnings = [DatasetWarning.model_validate(item) for item in dataset.metadata_json.get("warnings", [])]
    return DatasetDetail.model_validate(dataset).model_copy(update={"warnings": warnings})


async def upload_dataset(upload: UploadFile, db: Session, settings: Settings) -> DatasetUploadResponse:
    started = monotonic()
    safe_name = DatasetStorageService.normalize_filename(upload.filename)
    extension = _extension(upload.filename)
    if extension not in settings.allowed_dataset_extensions:
        raise UnsupportedDatasetTypeError("Unsupported dataset file type")
    allowed_mimes = {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel", ""}
    if (upload.content_type or "").lower() not in allowed_mimes:
        raise UnsupportedDatasetTypeError("File content type is inconsistent with CSV")
    logger.info("dataset_upload_started filename=%s", safe_name)
    storage = DatasetStorageService(settings)
    stored = await storage.save(upload, extension)
    try:
        duplicate = db.scalar(select(Dataset).where(Dataset.checksum_sha256 == stored.checksum))
        if duplicate is not None:
            storage.cleanup(stored.path)
            logger.info("dataset_duplicate_detected dataset_id=%s", duplicate.id)
            raise DuplicateDatasetError(duplicate.id)
        logger.info("dataset_parsing_started dataset_id=%s", stored.dataset_id)
        parsed = parse_csv(stored.path, settings)
        dataset = Dataset(
            id=stored.dataset_id,
            original_filename=stored.original_filename,
            stored_filename=stored.stored_filename,
            storage_key=stored.storage_key,
            file_extension=extension,
            mime_type="text/csv",
            file_size_bytes=stored.size,
            checksum_sha256=stored.checksum,
            row_count=parsed.row_count,
            column_count=len(parsed.columns),
            column_names=parsed.columns,
            delimiter=parsed.delimiter,
            encoding=parsed.encoding,
            status=DatasetStatus.ready,
            ingestion_version=settings.dataset_ingestion_version,
            preview_available=bool(parsed.preview),
            metadata_json={"warnings": parsed.warnings},
            preview_json=parsed.preview,
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        logger.info(
            "dataset_ingestion_completed dataset_id=%s size=%s rows=%s duration_ms=%s",
            dataset.id,
            dataset.file_size_bytes,
            dataset.row_count,
            round((monotonic() - started) * 1000),
        )
        detail = _detail(dataset)
        return DatasetUploadResponse(**detail.model_dump(), preview_rows=dataset.preview_json)
    except DuplicateDatasetError:
        raise
    except (InvalidDatasetError, UnsupportedDatasetTypeError):
        storage.cleanup(stored.path)
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        storage.cleanup(stored.path)
        raise DatasetStorageError("Dataset metadata could not be persisted") from exc
    except Exception:
        storage.cleanup(stored.path)
        raise


def list_datasets(
    db: Session, page: int, page_size: int, status: DatasetStatus | None, search: str | None, sort: str
) -> DatasetListResponse:
    filters = []
    if status is not None:
        filters.append(Dataset.status == status)
    if search:
        filters.append(Dataset.original_filename.ilike(f"%{search.strip()}%"))
    total = db.scalar(select(func.count()).select_from(Dataset).where(*filters)) or 0
    order = Dataset.created_at.asc() if sort == "oldest" else Dataset.created_at.desc()
    items = db.scalars(
        select(Dataset).where(*filters).order_by(order).offset((page - 1) * page_size).limit(page_size)
    ).all()
    dataset_ids = [item.id for item in items]
    schema_rows = db.execute(
        select(DatasetSchemaProfile.dataset_id, DatasetSchemaProfile.status).where(
            DatasetSchemaProfile.dataset_id.in_(dataset_ids),
            DatasetSchemaProfile.status != SchemaStatus.superseded,
        )
    ).all()
    schema_statuses = {dataset_id: status.value for dataset_id, status in schema_rows}
    quality_rows = db.execute(
        select(
            DatasetQualityReport.dataset_id,
            DatasetQualityReport.readiness_status,
            DatasetQualityReport.overall_score,
            DatasetQualityReport.blocker_count,
        ).where(
            DatasetQualityReport.dataset_id.in_(dataset_ids),
            DatasetQualityReport.status == QualityReportStatus.completed,
        )
    ).all()
    quality_statuses = {
        dataset_id: (status.value, score, blockers) for dataset_id, status, score, blockers in quality_rows
    }
    preparation_rows = db.execute(
        select(
            PreparedDataset.source_dataset_id,
            PreparedDataset.status,
            PreparedDataset.preparation_version,
            PreparedDataset.readiness_status,
        ).where(
            PreparedDataset.source_dataset_id.in_(dataset_ids),
            PreparedDataset.status.in_([PreparationStatus.completed, PreparationStatus.failed]),
        )
    ).all()
    preparation_statuses = {
        dataset_id: (status.value, version, readiness.value)
        for dataset_id, status, version, readiness in preparation_rows
    }
    return DatasetListResponse(
        items=[
            DatasetSummary.model_validate(item).model_copy(
                update={
                    "schema_status": schema_statuses.get(item.id, "not_analyzed"),
                    "quality_status": quality_statuses.get(item.id, ("not_analyzed", None, 0))[0],
                    "quality_score": quality_statuses.get(item.id, ("not_analyzed", None, 0))[1],
                    "quality_blockers": quality_statuses.get(item.id, ("not_analyzed", None, 0))[2],
                    "preparation_status": preparation_statuses.get(
                        item.id, ("not_prepared", None, "configuration_required")
                    )[0],
                    "preparation_version": preparation_statuses.get(
                        item.id, ("not_prepared", None, "configuration_required")
                    )[1],
                    "preparation_readiness": preparation_statuses.get(
                        item.id, ("not_prepared", None, "configuration_required")
                    )[2],
                }
            )
            for item in items
        ],
        pagination=PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=(total + page_size - 1) // page_size,
        ),
    )


def get_dataset(db: Session, dataset_id: str, include_archived: bool = True) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None or (not include_archived and dataset.status == DatasetStatus.archived):
        raise DatasetNotFoundError("Dataset was not found")
    return dataset


def dataset_detail(db: Session, dataset_id: str) -> DatasetDetail:
    return _detail(get_dataset(db, dataset_id))


def dataset_preview(db: Session, dataset_id: str, limit: int, maximum: int) -> DatasetPreviewResponse:
    dataset = get_dataset(db, dataset_id, include_archived=False)
    rows = dataset.preview_json[: min(limit, maximum)]
    return DatasetPreviewResponse(
        dataset_id=dataset.id,
        columns=dataset.column_names,
        rows=rows,
        returned_rows=len(rows),
        max_rows=maximum,
    )


def archive_dataset(db: Session, dataset_id: str, settings: Settings) -> DatasetArchiveResponse:
    dataset = get_dataset(db, dataset_id, include_archived=False)
    storage = DatasetStorageService(settings)
    storage_key = storage.archive(dataset.stored_filename)
    now = datetime.now(UTC)
    try:
        dataset.storage_key = storage_key
        dataset.status = DatasetStatus.archived
        dataset.deleted_at = now
        db.commit()
        logger.info("dataset_archived dataset_id=%s", dataset.id)
    except SQLAlchemyError as exc:
        db.rollback()
        storage.restore_archived(dataset.stored_filename)
        raise DatasetStorageError("Dataset archive metadata could not be updated") from exc
    return DatasetArchiveResponse(id=dataset.id, status="archived", deleted_at=now)


def dataset_stats(db: Session) -> DatasetStatsResponse:
    active = db.scalar(select(func.count()).select_from(Dataset).where(Dataset.status == DatasetStatus.ready)) or 0
    latest = db.scalar(select(Dataset).where(Dataset.status == DatasetStatus.ready).order_by(Dataset.created_at.desc()))
    return DatasetStatsResponse(
        active_datasets=active,
        latest_filename=latest.original_filename if latest else None,
        latest_upload_at=latest.created_at if latest else None,
    )
