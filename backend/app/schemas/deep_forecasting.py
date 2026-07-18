from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

DeepModelId = Literal["nhits", "temporal_fusion_transformer", "nbeats"]
DeepStatus = Literal[
    "unavailable",
    "dependency_missing",
    "planned",
    "infrastructure_ready",
    "training_ready",
    "experimental",
    "production_ready",
    "disabled",
]
Accelerator = Literal["auto", "cpu", "cuda", "mps"]
Scaler = Literal["none", "standard", "robust", "minmax", "median", "identity"]
TargetTransform = Literal["none", "log1p", "signed_log1p", "boxcox", "yeojohnson"]


class DeepForecastRuntimeConfig(BaseModel):
    enabled: bool = True
    engine: Literal["neuralforecast"] = "neuralforecast"
    random_seed: int = Field(default=42, ge=0, le=2**32 - 1)
    deterministic: bool = True
    accelerator: Accelerator = "auto"
    devices: int = Field(default=1, ge=1, le=64)
    cpu_fallback: bool = True
    num_workers: int = Field(default=0, ge=0, le=128)
    torch_num_threads: int = Field(default=4, ge=1, le=256)
    interop_threads: int = Field(default=1, ge=1, le=256)
    profiling_enabled: bool = False


class DeepForecastDataConfig(BaseModel):
    prepared_dataset_id: str | None = None
    target_column: str
    time_column: str
    group_columns: list[str]
    frequency: Literal["hourly", "daily", "weekly", "monthly"]
    forecast_horizon: int = Field(ge=1, le=365)
    input_size: int = Field(ge=1, le=365)
    step_size: int = Field(default=1, ge=1, le=365)
    historical_covariates: list[str] = Field(default_factory=list, max_length=200)
    future_covariates: list[str] = Field(default_factory=list, max_length=200)
    static_covariates: list[str] = Field(default_factory=list, max_length=200)
    scale_per_series: bool = True
    scaler_type: Scaler = "robust"
    target_transform: TargetTransform = "none"
    missing_target_policy: Literal["fail", "preparation_managed"] = "fail"
    duplicate_timestamp_policy: Literal["fail", "preparation_managed"] = "fail"
    irregular_frequency_policy: Literal["fail", "preparation_managed"] = "fail"

    @model_validator(mode="after")
    def disjoint_safe_columns(self) -> "DeepForecastDataConfig":
        categories = [self.historical_covariates, self.future_covariates, self.static_covariates]
        all_covariates = [name for values in categories for name in values]
        if self.target_column in all_covariates:
            raise ValueError("Target cannot be configured as a covariate")
        if len(all_covariates) != len(set(all_covariates)):
            raise ValueError("Deep covariate categories cannot overlap")
        if self.target_column == self.time_column or self.target_column in self.group_columns:
            raise ValueError("Target, time, and group columns must be distinct")
        if len(self.group_columns) != len(set(self.group_columns)):
            raise ValueError("Group columns must be unique")
        return self


class DeepForecastModelConfig(BaseModel):
    model_name: DeepModelId = "nhits"
    enabled: bool = True
    implementation_status: DeepStatus = "infrastructure_ready"
    input_size: int = Field(ge=1, le=365)
    horizon: int = Field(ge=1, le=365)
    loss_name: str = "mae"
    valid_loss_name: str = "mae"
    scaler_type: Scaler = "robust"
    max_steps: int = Field(default=1000, ge=1)
    learning_rate: float = Field(default=0.001, gt=0, le=1)
    batch_size: int = Field(default=32, ge=1)
    windows_batch_size: int = Field(default=1024, ge=1)
    random_seed: int = Field(default=42, ge=0)
    accelerator: Accelerator = "auto"
    devices: int = Field(default=1, ge=1)


class DeepForecastArtifactConfig(BaseModel):
    checksum_algorithm: Literal["sha256"] = "sha256"
    save_optimizer_state: bool = False
    max_checkpoints_per_run: int = Field(default=3, ge=1, le=20)
    environment_capture_enabled: bool = True


class DeepForecastLimitsConfig(BaseModel):
    max_rows: int
    max_series: int
    max_features: int
    max_horizon: int
    max_history_rows_per_series: int
    max_input_size: int
    minimum_history_multiplier: int


class DeepForecastModelDefinitionResponse(BaseModel):
    identifier: DeepModelId
    display_name: str
    family: str
    description: str
    implementation_status: DeepStatus
    enabled_by_default: bool
    dependency_name: str
    dependency_available: bool
    supported_frequencies: list[str]
    supports_grouped_series: bool
    supports_global_model: bool
    supports_per_group_model: bool
    supports_historical_covariates: bool
    supports_future_covariates: bool
    supports_static_covariates: bool
    supports_quantiles: bool
    supports_probabilistic_loss: bool
    supports_gpu: bool
    supports_cpu: bool
    supports_checkpointing: bool
    supports_early_stopping: bool
    supports_explainability: bool
    minimum_history_formula: str
    recommended_input_window: str
    recommended_horizon: str
    known_limitations: list[str]
    future_phase: str


class DeepForecastDependencyResponse(BaseModel):
    package_name: str
    installed: bool
    version: str | None
    minimum_supported_version: str | None
    maximum_tested_version: str | None
    compatible: bool
    import_error_category: str | None
    required: bool
    optional: bool
    models_affected: list[str]


class DeepForecastHardwareResponse(BaseModel):
    operating_system: str
    python_architecture: str
    cpu_logical_count: int
    configured_training_threads: int
    available_memory_bytes: int | None
    pytorch_available: bool
    cuda_available: bool
    cuda_device_count: int
    cuda_device_names: list[str]
    cuda_version: str | None
    mps_available: bool
    selected_accelerator: Literal["cpu", "cuda", "mps"]
    selected_device_count: int
    cpu_fallback_enabled: bool
    deterministic_mode_configured: bool


class DeepForecastLimitResponse(DeepForecastLimitsConfig):
    pass


class DeepForecastCapabilityResponse(BaseModel):
    enabled: bool
    engine: str
    infrastructure_status: str
    training_status: Literal["nhits_training_ready"] = "nhits_training_ready"
    selected_accelerator: str
    models: list[DeepForecastModelDefinitionResponse]
    dependencies: list[DeepForecastDependencyResponse]
    hardware: DeepForecastHardwareResponse
    limits: DeepForecastLimitResponse


class DeepForecastReadinessRequest(BaseModel):
    model_name: DeepModelId = "nhits"
    target_column: str | None = None
    time_column: str | None = None
    group_columns: list[str] | None = None
    horizon: int = Field(default=30, ge=1, le=365)
    input_size: int | None = Field(default=None, ge=1, le=365)
    historical_covariates: list[str] | None = Field(default=None, max_length=200)
    future_covariates: list[str] | None = Field(default=None, max_length=200)
    static_covariates: list[str] | None = Field(default=None, max_length=200)
    scaler_type: Scaler = "robust"
    scale_per_series: bool = True
    target_transform: TargetTransform = "none"
    accelerator: Accelerator = "auto"


class DeepForecastCovariateResponse(BaseModel):
    name: str
    source: str
    category: Literal["historical", "future", "static", "excluded"]
    data_type: str
    known_at_forecast_time: bool
    target_derived: bool
    leakage_status: str
    missing_rate: float
    cardinality: int
    series_variability: bool
    time_variability: bool
    approved_for_deep_forecasting: bool
    exclusion_reason: str | None
    future_coverage_status: str


class DeepForecastSeriesReadiness(BaseModel):
    series_id: str
    eligible: bool
    observation_count: int
    required_observations: int
    start: str
    end: str
    missing_target_count: int
    training_windows: int
    validation_windows: int
    test_windows: int
    failure_reasons: list[str]


class DeepForecastSequenceSummary(BaseModel):
    input_size: int
    horizon: int
    step_size: int
    minimum_history: int
    total_training_windows: int
    total_validation_windows: int
    total_test_windows: int
    expected_input_shape: list[int]
    expected_output_shape: list[int]
    validation_context_policy: str
    test_context_policy: str


class DeepForecastArtifactManifestResponse(BaseModel):
    logical_name: str
    artifact_type: str
    checksum: str
    checksum_algorithm: Literal["sha256"]
    size_bytes: int
    framework: str
    framework_version: str | None
    synthetic_data: bool
    created_at: datetime


class DeepForecastReadinessResponse(BaseModel):
    snapshot_id: str
    prepared_dataset_id: str
    readiness_status: Literal["ready", "ready_with_warnings", "blocked", "dependency_missing", "disabled"]
    preparation_status: str
    model_ready: bool
    deep_forecasting_ready: bool
    checksum_valid: bool
    source_checksum_valid: bool
    manifest_valid: bool
    split_manifest_valid: bool
    feature_catalog_valid: bool
    frequency_valid: bool
    target_valid: bool
    group_valid: bool
    future_covariates_valid: bool
    static_covariates_valid: bool
    sequence_windows_valid: bool
    minimum_history_valid: bool
    train_rows: int
    validation_rows: int
    test_rows: int
    series_count: int
    eligible_series_count: int
    ineligible_series_count: int
    feature_count: int
    historical_covariate_count: int
    future_covariate_count: int
    static_covariate_count: int
    target_column: str
    time_column: str
    frequency: str
    input_size: int
    horizon: int
    covariates: list[DeepForecastCovariateResponse]
    series: list[DeepForecastSeriesReadiness]
    sequence_summary: DeepForecastSequenceSummary
    warnings: list[str]
    blockers: list[str]
    synthetic_data: bool
    generated_at: datetime
    engine: str
    selected_accelerator: str
    dependency_status: str
    artifact_checksums: dict[str, str]
    training_executed: bool = False
    checkpoint_created: bool = False


class NHiTSTrainingRequest(BaseModel):
    prepared_dataset_id: str
    readiness_snapshot_id: str | None = None
    configuration: dict[str, object] = Field(default_factory=dict)


class DeepTrainingMetrics(BaseModel):
    mae: float | None
    rmse: float | None
    mape: float | None
    smape: float | None
    wape: float | None
    r2: float | None


class DeepTrainingExperimentResponse(BaseModel):
    experiment_id: str
    model_run_id: str
    prepared_dataset_id: str
    model_name: str
    status: str
    current_epoch: int | None
    max_steps: int
    selected_accelerator: str
    training_duration_ms: int
    checkpoint_available: bool
    checkpoint_checksum: str | None
    metrics: DeepTrainingMetrics | None
    failure_message: str | None
    created_at: datetime
    completed_at: datetime | None


class DeepTrainingListResponse(BaseModel):
    items: list[DeepTrainingExperimentResponse]
    total: int


class DeepCheckpointResumeRequest(BaseModel):
    model_run_id: str
    additional_steps: int = Field(ge=1, le=1_000_000)
    checkpoint_type: Literal["latest", "best"] = "latest"


class DeepCheckpointResumeResponse(BaseModel):
    source_model_run_id: str
    resumed_model_run_id: str
    status: str
    restored_checkpoint_checksum: str
    previous_steps: int
    requested_additional_steps: int
