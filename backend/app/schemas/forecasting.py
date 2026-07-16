from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

ModelId = Literal[
    "naive_last",
    "seasonal_naive",
    "moving_average",
    "drift",
    "simple_exponential_smoothing",
    "holt_linear",
    "holt_winters",
    "linear_regression",
    "ridge_regression",
    "lightgbm_regressor",
    "xgboost_regressor",
    "catboost_regressor",
]


class ForecastExperimentConfig(BaseModel):
    target_column: str | None = None
    forecast_horizon: int | None = Field(default=None, ge=1, le=365)
    selection_metric: Literal["wape", "mae", "rmse", "smape"] | None = None
    enabled_models: list[ModelId] = [
        "naive_last",
        "seasonal_naive",
        "moving_average",
        "drift",
        "simple_exponential_smoothing",
        "holt_linear",
        "holt_winters",
        "linear_regression",
        "ridge_regression",
    ]
    moving_average_windows: list[int] | None = None
    seasonal_period: int | None = Field(default=None, ge=2, le=366)
    backtest_folds: int | None = Field(default=None, ge=1, le=12)
    evaluate_per_group: bool = True
    include_exogenous_features: bool = True
    linear_feature_allowlist: list[str] | None = None
    notes: str | None = Field(default=None, max_length=1000)
    strategy: Literal["global", "per_group"] = "global"
    tuning_trials: int | None = Field(default=None, ge=1, le=100)
    tuning_timeout_seconds: int | None = Field(default=None, ge=10, le=3600)
    early_stopping_rounds: int | None = Field(default=None, ge=1, le=500)
    generate_shap: bool = True
    tuning_folds: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def unique_valid_values(self) -> "ForecastExperimentConfig":
        if not self.enabled_models or len(self.enabled_models) != len(set(self.enabled_models)):
            raise ValueError("Enabled models must be non-empty and unique")
        if self.moving_average_windows is not None and (
            not self.moving_average_windows or any(x < 1 for x in self.moving_average_windows)
        ):
            raise ValueError("Moving-average windows must be positive")
        return self


class ForecastExperimentCreateRequest(BaseModel):
    config: ForecastExperimentConfig = Field(default_factory=ForecastExperimentConfig)


class ForecastMetricSet(BaseModel):
    row_count: int
    mae: float | None = None
    rmse: float | None = None
    wape: float | None = None
    smape: float | None = None
    mase: float | None = None
    bias: float | None = None
    mean_error: float | None = None
    median_absolute_error: float | None = None
    warnings: list[str] = Field(default_factory=list)


class ResidualSummary(BaseModel):
    mean: float
    standard_deviation: float
    median: float
    minimum: float
    maximum: float
    positive_ratio: float
    autocorrelation_lag_1: float | None
    large_residual_count: int


class ForecastWarning(BaseModel):
    code: str
    message: str


class ForecastValidationIssue(BaseModel):
    code: str
    message: str
    blocking: bool = True


class ForecastExperimentSummary(BaseModel):
    id: str
    prepared_dataset_id: str
    experiment_version: int
    status: str
    target_column: str
    frequency: str
    selected_model_run_id: str | None
    created_at: datetime
    completed_at: datetime | None


class ForecastExperimentResponse(ForecastExperimentSummary):
    forecasting_engine_version: str
    date_column: str
    group_columns: list[str]
    forecast_horizon: int
    selection_metric: str
    random_seed: int
    configuration: dict[str, object]
    prepared_artifact_checksum: str
    source_dataset_checksum: str
    train_start: str
    train_end: str
    validation_start: str
    validation_end: str
    test_start: str
    test_end: str
    backtest_fold_count: int
    validation_completed_at: datetime | None
    test_evaluated_at: datetime | None
    failure_message: str | None
    metadata: dict[str, object]


class ForecastExperimentHistoryResponse(BaseModel):
    items: list[ForecastExperimentSummary]


class ForecastModelDefinition(BaseModel):
    id: str
    name: str
    family: str
    description: str
    supports_groups: bool
    supports_trend: bool
    supports_seasonality: bool
    enabled: bool = True
    supported_feature_types: list[str] = Field(default_factory=list)
    categorical_support: bool = False
    tuning_support: bool = False
    early_stopping_support: bool = False
    explanation_support: bool = False
    dependency_available: bool = True
    dependency_version: str | None = None
    default_parameters: dict[str, object] = Field(default_factory=dict)


class ForecastModelRunSummary(BaseModel):
    id: str
    experiment_id: str
    model_name: str
    model_family: str
    status: str
    rank: int | None
    selection_score: float | None
    selected: bool
    validation_metrics: ForecastMetricSet | None
    backtest_metrics: ForecastMetricSet | None
    training_duration_ms: int
    backtest_duration_ms: int
    failure_message: str | None
    tuning_trial_count: int = 0
    failed_trial_count: int = 0
    tuning_duration_ms: int = 0
    best_iteration: int | None = None
    feature_count: int = 0
    strategy: str = "global"
    explanation_available: bool = False


class ForecastModelRunResponse(ForecastModelRunSummary):
    model_version: str
    hyperparameters: dict[str, object]
    fitted_on: str
    supports_groups: bool
    supports_trend: bool
    supports_seasonality: bool
    artifact_checksum: str | None
    per_fold_metrics: list[dict[str, object]]
    per_group_metrics: list[dict[str, object]]
    residual_summary: ResidualSummary | None
    completed_at: datetime | None


class ForecastEvaluationResponse(BaseModel):
    id: str
    model_run_id: str
    evaluation_type: str
    split_name: str
    fold_number: int | None
    group_value: str | None
    horizon: int
    metrics: ForecastMetricSet
    created_at: datetime


class ForecastComparisonResponse(BaseModel):
    experiment_id: str
    selected_model_run_id: str | None
    selection_method: str
    items: list[ForecastModelRunSummary]


class ForecastPredictionRow(BaseModel):
    date: str
    actual: float
    prediction: float
    residual: float
    split: str
    fold: int | None = None
    group: str | None = None


class ForecastPredictionListResponse(BaseModel):
    experiment_id: str
    model_run_id: str
    split: str
    items: list[ForecastPredictionRow]
    page: int
    page_size: int
    total: int
    pages: int


class ForecastArtifactResponse(BaseModel):
    id: str
    model_run_id: str
    artifact_type: str
    checksum: str
    row_count: int
    created_at: datetime


class GroupMetricSummary(BaseModel):
    group: str
    metrics: ForecastMetricSet


class ForecastStatsResponse(BaseModel):
    total_experiments: int
    completed_experiments: int
    failed_experiments: int
    selected_model_distribution: dict[str, int]
    average_test_wape: float | None
    datasets_awaiting_forecasting: int
    latest_experiment_status: str | None


class TuningTrialSummary(BaseModel):
    trial_number: int
    status: str
    parameters: dict[str, object]
    backtest_metric: float | None
    validation_metric: float | None
    duration_ms: int
    failure_message: str | None


class TuningSummaryResponse(BaseModel):
    model_run_id: str
    method: str | None
    completed_trials: int
    failed_trials: int
    best_score: float | None
    best_parameters: dict[str, object]
    duration_ms: int
    items: list[TuningTrialSummary]


class FeatureImportanceItem(BaseModel):
    feature: str
    native_importance: float | None
    shap_importance: float | None
    feature_type: str
    leakage_status: str


class FeatureImportanceResponse(BaseModel):
    model_run_id: str
    items: list[FeatureImportanceItem]
    disclaimer: str = "Feature contribution does not prove causation."


class ShapFeatureSummary(BaseModel):
    feature: str
    mean_absolute_shap: float
    mean_shap: float
    direction: str


class ShapExplanationResponse(BaseModel):
    model_run_id: str
    sample_rows: int
    items: list[ShapFeatureSummary]
    disclaimer: str = "SHAP describes model contribution, not causal effect."


class GradientBoostingStatsResponse(BaseModel):
    completed_experiments: int
    model_wins: dict[str, int]
    average_tuning_duration_ms: float | None
    average_improvement_over_baseline: float | None
    failed_model_count: int
