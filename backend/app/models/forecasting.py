import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ForecastExperimentStatus(StrEnum):
    pending = "pending"
    validating = "validating"
    training = "training"
    backtesting = "backtesting"
    selecting = "selecting"
    test_evaluating = "test_evaluating"
    completed = "completed"
    failed = "failed"


class ForecastModelStatus(StrEnum):
    pending = "pending"
    fitting = "fitting"
    backtesting = "backtesting"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class ForecastExperiment(Base):
    __tablename__ = "forecast_experiments"
    __table_args__ = (
        UniqueConstraint("prepared_dataset_id", "experiment_version"),
        Index("ix_forecast_prepared_status", "prepared_dataset_id", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prepared_dataset_id: Mapped[str] = mapped_column(ForeignKey("prepared_datasets.id", ondelete="CASCADE"), index=True)
    experiment_version: Mapped[int] = mapped_column(Integer)
    forecasting_engine_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[ForecastExperimentStatus] = mapped_column(Enum(ForecastExperimentStatus), index=True)
    target_column: Mapped[str] = mapped_column(String(255))
    date_column: Mapped[str] = mapped_column(String(255))
    group_columns_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    frequency: Mapped[str] = mapped_column(String(20))
    forecast_horizon: Mapped[int] = mapped_column(Integer)
    selection_metric: Mapped[str] = mapped_column(String(20))
    random_seed: Mapped[int] = mapped_column(Integer)
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    configuration_hash: Mapped[str] = mapped_column(String(64))
    prepared_artifact_checksum: Mapped[str] = mapped_column(String(64))
    source_dataset_checksum: Mapped[str] = mapped_column(String(64))
    train_start: Mapped[str] = mapped_column(String(40))
    train_end: Mapped[str] = mapped_column(String(40))
    validation_start: Mapped[str] = mapped_column(String(40))
    validation_end: Mapped[str] = mapped_column(String(40))
    test_start: Mapped[str] = mapped_column(String(40))
    test_end: Mapped[str] = mapped_column(String(40))
    backtest_fold_count: Mapped[int] = mapped_column(Integer)
    selected_model_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    validation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    test_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    model_runs: Mapped[list["ForecastModelRun"]] = relationship(cascade="all, delete-orphan")


class ForecastModelRun(Base):
    __tablename__ = "forecast_model_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey("forecast_experiments.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(80))
    model_family: Mapped[str] = mapped_column(String(50))
    model_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[ForecastModelStatus] = mapped_column(Enum(ForecastModelStatus), index=True)
    hyperparameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    fitted_on: Mapped[str] = mapped_column(String(30), default="train")
    supports_groups: Mapped[bool] = mapped_column(Boolean)
    supports_trend: Mapped[bool] = mapped_column(Boolean)
    supports_seasonality: Mapped[bool] = mapped_column(Boolean)
    artifact_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    artifact_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    training_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    backtest_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    validation_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    aggregate_backtest_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    per_fold_metrics_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    per_group_metrics_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    residual_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selection_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tuning_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tuning_trial_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_trial_count: Mapped[int] = mapped_column(Integer, default=0)
    tuning_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    best_iteration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    explanation_available: Mapped[bool] = mapped_column(Boolean, default=False)
    global_model: Mapped[bool] = mapped_column(Boolean, default=True)
    strategy: Mapped[str] = mapped_column(String(20), default="global")
    dependency_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    evaluations: Mapped[list["ForecastEvaluation"]] = relationship(cascade="all, delete-orphan")
    artifacts: Mapped[list["ForecastPredictionArtifact"]] = relationship(cascade="all, delete-orphan")
    tuning_trials: Mapped[list["ForecastTuningTrial"]] = relationship(cascade="all, delete-orphan")


class ForecastTuningTrial(Base):
    __tablename__ = "forecast_tuning_trials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_model_runs.id", ondelete="CASCADE"), index=True)
    trial_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    backtest_metric: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_metric: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ForecastEvaluation(Base):
    __tablename__ = "forecast_evaluations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_model_runs.id", ondelete="CASCADE"), index=True)
    evaluation_type: Mapped[str] = mapped_column(String(30), index=True)
    split_name: Mapped[str] = mapped_column(String(30))
    fold_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    horizon: Mapped[int] = mapped_column(Integer)
    row_count: Mapped[int] = mapped_column(Integer)
    mae: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    wape: Mapped[float | None] = mapped_column(Float)
    smape: Mapped[float | None] = mapped_column(Float)
    mase: Mapped[float | None] = mapped_column(Float)
    bias: Mapped[float | None] = mapped_column(Float)
    mean_error: Mapped[float | None] = mapped_column(Float)
    median_absolute_error: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ForecastPredictionArtifact(Base):
    __tablename__ = "forecast_prediction_artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id: Mapped[str] = mapped_column(ForeignKey("forecast_experiments.id", ondelete="CASCADE"), index=True)
    model_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_model_runs.id", ondelete="CASCADE"), index=True)
    artifact_type: Mapped[str] = mapped_column(String(40), index=True)
    storage_key: Mapped[str] = mapped_column(String(255))
    checksum: Mapped[str] = mapped_column(String(64))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
