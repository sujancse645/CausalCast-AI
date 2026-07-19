from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProductionDatasetSummary(BaseModel):
    id: str
    name: str
    model_name: str
    model_type: str
    target: str
    frequency: str
    default_horizon: int
    model_available: bool
    data_available: bool


class ProductionDatasetMetadata(ProductionDatasetSummary):
    features: list[str]
    series_dimension: str | None
    series_count: int | None
    example_series: list[str]
    prediction_kind: str
    metrics: dict[str, float]
    model_checksum: str | None


class ProductionModelSummary(BaseModel):
    id: str
    dataset_id: str
    name: str
    model_type: str
    selected_metric: str
    selected_metric_value: float
    checksum: str
    loaded: bool


class ProductionForecastRequest(BaseModel):
    dataset: str = Field(min_length=2, max_length=100)
    horizon: int | None = Field(default=None, ge=1, le=365)
    series: str | None = Field(default=None, max_length=300)

    @field_validator("dataset", "series")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class ProductionPrediction(BaseModel):
    timestamp: datetime
    prediction: float
    actual: float | None


class ProductionForecastResponse(BaseModel):
    dataset: str
    dataset_name: str
    model_name: str
    model_type: str
    model_checksum: str
    prediction_kind: str
    target: str
    frequency: str
    series: str | None
    horizon: int
    rows_used: int
    prediction_start: datetime
    prediction_end: datetime
    predictions: list[ProductionPrediction]
    metrics: dict[str, float]
    runtime_ms: int
    model_loaded_from_disk: bool
    generated_at: datetime


class ProductionReportResponse(BaseModel):
    dataset: str
    selected_model: str
    selected_metrics: dict[str, float]
    comparisons: list[dict[str, float | str]]
