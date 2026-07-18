from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    app_name: str = "CausalCast AI"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "sqlite:///./causalcast.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    dataset_storage_root: Path = Path("../data/raw")
    dataset_upload_dir: str = "uploads"
    dataset_quarantine_dir: str = "quarantine"
    dataset_archive_dir: str = "archived"
    max_upload_size_mb: int = 25
    allowed_dataset_extensions: list[str] = ["csv"]
    dataset_preview_rows: int = 20
    dataset_max_columns: int = 500
    dataset_max_rows_for_preview_scan: int = 10000
    dataset_ingestion_version: int = 1
    dataset_delete_mode: Literal["archive"] = "archive"
    dataset_max_cell_length: int = 500
    schema_inference_sample_rows: int = 5000
    schema_inference_preview_values: int = 10
    schema_inference_min_confidence: float = 0.60
    schema_inference_auto_confirm_threshold: float = 0.92
    schema_inference_ambiguity_margin: float = 0.10
    schema_inference_version: str = "1.0"
    schema_inference_max_cell_length: int = 200
    schema_inference_max_unique_tracking: int = 10000
    data_quality_engine_version: str = "1.0"
    data_quality_max_scan_rows: int = 250000
    data_quality_sample_rows: int = 10000
    data_quality_evidence_rows: int = 10
    data_quality_max_findings_per_rule: int = 100
    data_quality_missing_warning_threshold: float = 0.05
    data_quality_missing_error_threshold: float = 0.25
    data_quality_missing_blocker_threshold: float = 0.60
    data_quality_duplicate_warning_threshold: float = 0.01
    data_quality_duplicate_error_threshold: float = 0.10
    data_quality_outlier_warning_threshold: float = 0.02
    data_quality_outlier_error_threshold: float = 0.10
    data_quality_high_cardinality_threshold: float = 0.80
    data_quality_near_constant_threshold: float = 0.98
    data_quality_date_parse_threshold: float = 0.95
    data_quality_temporal_gap_warning_multiplier: float = 2.0
    data_quality_relationship_tolerance: float = 0.15
    data_quality_score_blocker_cap: int = 49
    data_quality_scan_chunk_size: int = 10000
    preparation_engine_version: str = "1.0"
    preparation_storage_root: Path = Path("../data/processed")
    preparation_default_format: Literal["csv"] = "csv"
    preparation_max_rows: int = 500000
    preparation_chunk_size: int = 25000
    preparation_preview_rows: int = 50
    preparation_min_periods: int = 10
    preparation_default_frequency: str = "daily"
    preparation_default_forecast_horizon: int = 30
    preparation_default_train_ratio: float = 0.70
    preparation_default_validation_ratio: float = 0.15
    preparation_default_test_ratio: float = 0.15
    preparation_min_train_rows: int = 6
    preparation_min_validation_rows: int = 2
    preparation_min_test_rows: int = 2
    preparation_max_lag: int = 90
    preparation_max_rolling_window: int = 90
    preparation_max_groups: int = 1000
    preparation_allow_quality_override: bool = False
    preparation_default_missing_period_policy: str = "preserve"
    preparation_default_duplicate_policy: str = "aggregate"
    preparation_random_seed: int = 42
    forecast_engine_version: str = "1.0"
    forecast_artifact_root: Path = Path("../artifacts")
    forecast_random_seed: int = 42
    forecast_default_horizon: int = 30
    forecast_default_selection_metric: Literal["wape", "mae", "rmse", "smape"] = "wape"
    forecast_backtest_folds: int = 5
    forecast_min_train_periods: int = 90
    forecast_min_validation_periods: int = 14
    forecast_min_test_periods: int = 14
    forecast_max_models_per_experiment: int = 10
    forecast_max_groups: int = 1000
    forecast_max_training_seconds: int = 300
    forecast_moving_average_windows: list[int] = [7, 14, 28]
    forecast_seasonal_period_daily: int = 7
    forecast_seasonal_period_weekly: int = 52
    forecast_seasonal_period_monthly: int = 12
    forecast_enable_ets: bool = True
    forecast_enable_linear_baselines: bool = True
    forecast_save_residuals: bool = True
    forecast_metric_epsilon: float = 0.00000001
    gbm_engine_version: str = "1.0"
    gbm_random_seed: int = 42
    gbm_tuning_trials: int = 25
    gbm_tuning_timeout_seconds: int = 300
    gbm_primary_metric: Literal["wape", "mae", "rmse", "smape"] = "wape"
    gbm_early_stopping_rounds: int = 50
    gbm_max_depth_min: int = 3
    gbm_max_depth_max: int = 10
    gbm_learning_rate_min: float = 0.01
    gbm_learning_rate_max: float = 0.20
    gbm_estimators_min: int = 100
    gbm_estimators_max: int = 1500
    gbm_min_child_weight_min: int = 1
    gbm_min_child_weight_max: int = 20
    gbm_subsample_min: float = 0.60
    gbm_colsample_min: float = 0.60
    gbm_reg_alpha_max: float = 10
    gbm_reg_lambda_max: float = 20
    gbm_enable_lightgbm: bool = True
    gbm_enable_xgboost: bool = True
    gbm_enable_catboost: bool = True
    gbm_enable_shap: bool = True
    gbm_shap_sample_rows: int = 500
    gbm_n_jobs: int = 4
    gbm_max_memory_mb: int = 4096
    deep_forecasting_enabled: bool = True
    deep_forecasting_engine: Literal["neuralforecast"] = "neuralforecast"
    deep_forecasting_engine_version: str = "1.0"
    deep_forecasting_random_seed: int = 42
    deep_forecasting_deterministic: bool = True
    deep_forecasting_accelerator: Literal["auto", "cpu", "cuda", "mps"] = "auto"
    deep_forecasting_devices: int = 1
    deep_forecasting_cpu_fallback: bool = True
    deep_forecasting_num_workers: int = 0
    deep_forecasting_torch_num_threads: int = 4
    deep_forecasting_interop_threads: int = 1
    deep_forecasting_default_model: Literal["nhits", "temporal_fusion_transformer", "nbeats"] = "nhits"
    deep_forecasting_enable_nhits: bool = True
    deep_forecasting_enable_tft: bool = False
    deep_forecasting_enable_nbeats: bool = False
    deep_forecasting_default_horizon: int = 30
    deep_forecasting_default_input_size_multiplier: int = 4
    deep_forecasting_min_input_size: int = 28
    deep_forecasting_max_input_size: int = 365
    deep_forecasting_min_history_multiplier: int = 3
    deep_forecasting_default_scaler: Literal["none", "standard", "robust", "minmax", "median", "identity"] = "robust"
    deep_forecasting_scale_per_series: bool = True
    deep_forecasting_allow_global_scaling: bool = False
    deep_forecasting_target_transform: Literal["none", "log1p", "signed_log1p", "boxcox", "yeojohnson"] = "none"
    deep_forecasting_max_series: int = 500
    deep_forecasting_max_rows: int = 1000000
    deep_forecasting_max_features: int = 200
    deep_forecasting_max_horizon: int = 365
    deep_forecasting_max_history_rows_per_series: int = 10000
    deep_forecasting_checkpoints_enabled: bool = True
    deep_forecasting_max_checkpoints_per_run: int = 3
    deep_forecasting_save_optimizer_state: bool = False
    deep_forecasting_artifact_checksum_algorithm: Literal["sha256"] = "sha256"
    deep_forecasting_fail_on_missing_future_covariates: bool = True
    deep_forecasting_fail_on_duplicate_timestamps: bool = True
    deep_forecasting_fail_on_irregular_frequency: bool = True
    deep_forecasting_allow_missing_targets: bool = False
    deep_forecasting_log_progress: bool = False
    deep_forecasting_log_every_n_steps: int = 50
    deep_forecasting_enable_profiling: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{os.environ.get('APP_ENV', 'development')}"),
        extra="ignore",
        case_sensitive=False,
        secrets_dir="/run/secrets" if os.path.exists("/run/secrets") else None
    )

    @field_validator("cors_origins", "allowed_dataset_extensions", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("forecast_moving_average_windows", mode="before")
    @classmethod
    def parse_integer_list(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value

    @field_validator("max_upload_size_mb", "dataset_preview_rows", "dataset_max_columns")
    @classmethod
    def positive_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Dataset limits must be positive")
        return value

    @field_validator(
        "deep_forecasting_devices",
        "deep_forecasting_torch_num_threads",
        "deep_forecasting_interop_threads",
        "deep_forecasting_default_horizon",
        "deep_forecasting_default_input_size_multiplier",
        "deep_forecasting_min_input_size",
        "deep_forecasting_max_input_size",
        "deep_forecasting_min_history_multiplier",
        "deep_forecasting_max_series",
        "deep_forecasting_max_rows",
        "deep_forecasting_max_features",
        "deep_forecasting_max_horizon",
        "deep_forecasting_max_history_rows_per_series",
        "deep_forecasting_max_checkpoints_per_run",
        "deep_forecasting_log_every_n_steps",
    )
    @classmethod
    def positive_deep_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Deep forecasting limits must be positive")
        return value

    @field_validator("deep_forecasting_num_workers")
    @classmethod
    def nonnegative_deep_workers(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Deep forecasting workers cannot be negative")
        return value

    @field_validator(
        "schema_inference_min_confidence",
        "schema_inference_auto_confirm_threshold",
        "schema_inference_ambiguity_margin",
    )
    @classmethod
    def probability_limits(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("Schema confidence settings must be between zero and one")
        return value

    @field_validator(
        "data_quality_missing_warning_threshold",
        "data_quality_missing_error_threshold",
        "data_quality_missing_blocker_threshold",
        "data_quality_duplicate_warning_threshold",
        "data_quality_duplicate_error_threshold",
        "data_quality_outlier_warning_threshold",
        "data_quality_outlier_error_threshold",
        "data_quality_high_cardinality_threshold",
        "data_quality_near_constant_threshold",
        "data_quality_date_parse_threshold",
        "data_quality_relationship_tolerance",
    )
    @classmethod
    def quality_probability_limits(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("Data-quality ratio settings must be between zero and one")
        return value

    @model_validator(mode="after")
    def secure_production_defaults(self) -> "Settings":
        if self.app_env == "production" and self.debug:
            raise ValueError("DEBUG must be false in production")
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not permitted")
        if self.deep_forecasting_min_input_size > self.deep_forecasting_max_input_size:
            raise ValueError("Deep minimum input size cannot exceed maximum input size")
        if self.deep_forecasting_default_horizon > self.deep_forecasting_max_horizon:
            raise ValueError("Deep default horizon exceeds the configured maximum")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
