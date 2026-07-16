from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Frequency = Literal["hourly", "daily", "weekly", "monthly", "quarterly"]


class PreparationConfig(BaseModel):
    target_column: str
    date_column: str
    group_columns: list[str] = Field(default_factory=list)
    frequency: Frequency = "daily"
    forecast_horizon: int = Field(default=30, ge=1, le=365)
    aggregation_rules: dict[str, Literal["sum", "mean", "last", "min", "max"]] = Field(default_factory=dict)
    duplicate_period_policy: Literal["aggregate", "reject"] = "aggregate"
    missing_period_policy: Literal["preserve", "insert_null", "insert_zero_for_flow_metrics", "reject"] = "preserve"
    missing_target_policy: Literal["preserve", "drop_rows_missing_target"] = "drop_rows_missing_target"
    lag_periods: list[int] = Field(default_factory=lambda: [1, 7, 14, 28])
    rolling_windows: list[int] = Field(default_factory=lambda: [7, 28])
    rolling_statistics: list[Literal["mean", "sum", "min", "max"]] = ["mean"]
    include_calendar_features: bool = True
    include_trend_features: bool = True
    include_holiday_features: bool = False
    holiday_dates: list[str] = Field(default_factory=list)
    include_promotion_features: bool = True
    include_derived_metrics: bool = True
    include_missingness_indicators: bool = True
    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    train_end_date: str | None = None
    validation_end_date: str | None = None
    test_end_date: str | None = None
    backtest_folds: int = Field(default=3, ge=0, le=12)
    quality_override: bool = False
    quality_override_reason: str | None = Field(default=None, max_length=500)
    output_format: Literal["csv"] = "csv"

    @model_validator(mode="after")
    def validate_config(self) -> "PreparationConfig":
        if abs(self.train_ratio + self.validation_ratio + self.test_ratio - 1) > 1e-6:
            raise ValueError("Train, validation, and test ratios must total 1")
        if min(self.train_ratio, self.validation_ratio, self.test_ratio) <= 0:
            raise ValueError("Split ratios must be positive")
        if len(set(self.group_columns)) != len(self.group_columns):
            raise ValueError("Group columns must be unique")
        if any(value < 1 for value in self.lag_periods + self.rolling_windows):
            raise ValueError("Lag periods and rolling windows must be positive")
        return self


class PreparationCreateRequest(BaseModel):
    config: PreparationConfig


class PreparationWarning(BaseModel):
    code: str
    message: str


class PreparedFeatureResponse(BaseModel):
    id: str
    feature_name: str
    source_columns: list[str]
    feature_type: str
    transformation_type: str
    semantic_role: str
    physical_type: str
    availability_type: str
    leakage_risk: str
    included: bool
    generated: bool
    parameters: dict[str, object]
    lineage: dict[str, object]
    description: str


class SplitDefinition(BaseModel):
    name: Literal["train", "validation", "test"]
    start: str
    end: str
    rows: int


class BacktestFoldDefinition(BaseModel):
    fold: int
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str


class PreparationSummary(BaseModel):
    id: str
    source_dataset_id: str
    preparation_version: int
    status: str
    readiness_status: str
    row_count: int
    column_count: int
    feature_count: int
    frequency: str
    created_at: datetime


class PreparationResponse(PreparationSummary):
    preparation_engine_version: str
    source_schema_version: int
    source_quality_report_version: int
    source_checksum: str
    prepared_checksum: str | None
    target_column: str
    date_column: str
    group_columns: list[str]
    forecast_horizon: int
    train_rows: int
    validation_rows: int
    test_rows: int
    dropped_rows: int
    generated_rows: int
    duration_ms: int
    warnings: list[PreparationWarning]
    configuration: PreparationConfig
    completed_at: datetime | None


class PreparationHistoryResponse(BaseModel):
    items: list[PreparationSummary]


class FeatureCatalogResponse(BaseModel):
    prepared_dataset_id: str
    items: list[PreparedFeatureResponse]


class PreparationSplitResponse(BaseModel):
    prepared_dataset_id: str
    splits: list[SplitDefinition]
    backtest_folds: list[BacktestFoldDefinition]


class PreparationPreviewResponse(BaseModel):
    prepared_dataset_id: str
    columns: list[str]
    rows: list[dict[str, str | None]]
    returned_rows: int


class PreparationStatsResponse(BaseModel):
    total_prepared_datasets: int
    model_ready_datasets: int
    failed_preparations: int
    average_feature_count: float | None
    average_duration_ms: float | None
    datasets_awaiting_preparation: int
