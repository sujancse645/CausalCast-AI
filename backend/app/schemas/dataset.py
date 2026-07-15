from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DatasetStatusValue = Literal["uploading", "validating", "ready", "failed", "archived"]


class DatasetWarning(BaseModel):
    code: str
    message: str


class DatasetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    file_extension: str
    mime_type: str
    file_size_bytes: int
    row_count: int
    column_count: int
    status: DatasetStatusValue
    created_at: datetime
    preview_available: bool


class DatasetDetail(DatasetSummary):
    checksum_sha256: str
    column_names: list[str]
    delimiter: str | None
    encoding: str | None
    updated_at: datetime
    deleted_at: datetime | None
    ingestion_version: int
    source_type: str
    warnings: list[DatasetWarning] = []


class DatasetUploadResponse(DatasetDetail):
    preview_rows: list[dict[str, str | None]]


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict[str, str | None]]
    returned_rows: int
    max_rows: int


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class DatasetListResponse(BaseModel):
    items: list[DatasetSummary]
    pagination: PaginationMetadata


class DatasetArchiveResponse(BaseModel):
    id: str
    status: Literal["archived"]
    deleted_at: datetime


class DuplicateDatasetResponse(BaseModel):
    detail: str
    existing_dataset_id: str


class DatasetErrorResponse(BaseModel):
    detail: str


class DatasetStatsResponse(BaseModel):
    active_datasets: int = Field(ge=0)
    latest_filename: str | None
    latest_upload_at: datetime | None
    ingestion_status: Literal["operational"] = "operational"
