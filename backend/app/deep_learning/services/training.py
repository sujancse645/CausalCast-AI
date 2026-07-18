import csv
import hashlib
import json
import logging
import os
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.deep_learning.config.nhits import NHiTSConfig
from app.deep_learning.trainers.nhits import NHiTSTrainer
from app.models.forecasting import (
    DeepForecastCheckpoint,
    DeepForecastReadinessSnapshot,
    ForecastExperiment,
    ForecastExperimentStatus,
    ForecastModelRun,
    ForecastModelStatus,
)
from app.models.preparation import PreparedDataset
from app.schemas.deep_forecasting import (
    DeepCheckpointResumeRequest,
    DeepCheckpointResumeResponse,
    DeepTrainingExperimentResponse,
    DeepTrainingListResponse,
    DeepTrainingMetrics,
    NHiTSTrainingRequest,
)
from app.services.deep_forecasting.data_pipeline import FREQUENCY_ALIASES, _series_id
from app.services.deep_forecasting.hardware_service import hardware_report
from app.services.preparation_storage_service import PreparationStorageService

logger = logging.getLogger(__name__)


class DeepTrainingService:
    """Coordinates governed deep training with existing experiment persistence."""

    def __init__(self, db: Session, settings: Settings, trainer: NHiTSTrainer | None = None) -> None:
        self.db = db
        self.settings = settings
        self.trainer = trainer or NHiTSTrainer()

    def train_nhits(self, request: NHiTSTrainingRequest) -> DeepTrainingExperimentResponse:
        config = NHiTSConfig.model_validate(request.configuration)
        prepared = self.db.get(PreparedDataset, request.prepared_dataset_id)
        if not prepared:
            raise FileNotFoundError("Prepared dataset was not found")
        readiness = self._readiness(request.prepared_dataset_id, request.readiness_snapshot_id)
        if readiness.readiness_status not in {"ready", "ready_with_warnings"}:
            raise ValueError("Deep readiness must pass before training")
        report = readiness.report_json
        if config.forecast_horizon != int(report["horizon"]) or config.input_size != int(report["input_size"]):
            raise ValueError("Training horizon and input size must match the governed readiness snapshot")
        experiment, run = self._create_records(prepared, readiness, config)
        artifact_directory = self._artifact_directory(experiment.id, run.id)
        try:
            train, validation, static = self._frames(prepared, readiness)
            hardware = hardware_report(self.settings, config.accelerator)
            run.accelerator = hardware.selected_accelerator
            run.device_count = hardware.selected_device_count
            result = self.trainer.train(
                config=config,
                training_frame=train,
                validation_frame=validation,
                static_frame=static,
                historical_covariates=list(readiness.historical_covariates_json),
                future_covariates=list(readiness.future_covariates_json),
                static_covariates=list(readiness.static_covariates_json),
                frequency=FREQUENCY_ALIASES[prepared.frequency.lower()],
                accelerator=hardware.selected_accelerator,
                artifact_directory=artifact_directory,
            )
            self._write_artifacts(artifact_directory, config, result, hardware.model_dump(mode="json"))
            relative_checkpoint = str(
                result.checkpoint_path.relative_to(self.settings.forecast_artifact_root.resolve())
            ).replace("\\", "/")
            run.status = ForecastModelStatus.completed
            run.deep_model_status = "completed"
            run.training_duration_ms = result.training_duration_ms
            run.validation_metrics_json = result.metrics
            run.parameter_count = result.parameter_count
            run.checkpoint_available = True
            run.checkpoint_count = 1
            run.checkpoint_checksum = result.checkpoint_checksum
            run.artifact_storage_key = relative_checkpoint
            run.artifact_checksum = result.checkpoint_checksum
            run.completed_at = datetime.now(UTC)
            experiment.status = ForecastExperimentStatus.completed
            experiment.completed_at = run.completed_at
            checkpoint_size = sum(file.stat().st_size for file in result.checkpoint_path.rglob("*") if file.is_file())
            self.db.add(
                DeepForecastCheckpoint(
                    model_run_id=run.id,
                    checkpoint_type="latest",
                    global_step=config.max_steps,
                    monitored_metric="validation_mae",
                    monitored_value=result.metrics.get("mae"),
                    checksum=result.checkpoint_checksum,
                    file_size_bytes=checkpoint_size,
                    framework_version=run.training_framework_version,
                )
            )
            self.db.commit()
        except Exception as exc:
            logger.exception("N-HiTS training failed", extra={"experiment_id": experiment.id, "model_run_id": run.id})
            self.db.rollback()
            persisted_experiment = self.db.get(ForecastExperiment, experiment.id)
            persisted_run = self.db.get(ForecastModelRun, run.id)
            if persisted_experiment and persisted_run:
                persisted_experiment.status = ForecastExperimentStatus.failed
                persisted_experiment.failure_message = self._safe_failure(exc)
                persisted_run.status = ForecastModelStatus.failed
                persisted_run.deep_model_status = "failed"
                persisted_run.failure_message = self._safe_failure(exc)
                persisted_run.completed_at = datetime.now(UTC)
                self.db.commit()
            raise
        return self._response(run)

    def list_experiments(self, limit: int = 100) -> DeepTrainingListResponse:
        runs = self.db.scalars(
            select(ForecastModelRun)
            .where(ForecastModelRun.model_family == "deep_forecasting")
            .order_by(ForecastModelRun.created_at.desc())
            .limit(limit)
        ).all()
        return DeepTrainingListResponse(items=[self._response(item) for item in runs], total=len(runs))

    def get(self, identifier: str) -> DeepTrainingExperimentResponse:
        run = self.db.get(ForecastModelRun, identifier)
        if not run:
            experiment = self.db.get(ForecastExperiment, identifier)
            run = experiment.model_runs[0] if experiment and experiment.model_runs else None
        if not run or run.model_family != "deep_forecasting":
            raise FileNotFoundError("Deep experiment was not found")
        return self._response(run)

    def resume(self, request: DeepCheckpointResumeRequest) -> DeepCheckpointResumeResponse:
        source = self.db.get(ForecastModelRun, request.model_run_id)
        if (
            not source
            or not source.checkpoint_available
            or not source.artifact_storage_key
            or not source.checkpoint_checksum
        ):
            raise FileNotFoundError("A resumable checkpoint was not found")
        path = (self.settings.forecast_artifact_root.resolve() / source.artifact_storage_key).resolve()
        root = self.settings.forecast_artifact_root.resolve()
        if root not in path.parents or not path.is_dir():
            raise FileNotFoundError("Checkpoint is unavailable")
        from neuralforecast import NeuralForecast

        loaded = NeuralForecast.load(str(path))
        if not loaded.models:
            raise ValueError("Checkpoint contains no governed model")
        previous_steps = int(source.hyperparameters_json.get("max_steps", 0))
        loaded.models[0].max_steps = request.additional_steps
        resumed = ForecastModelRun(
            experiment_id=source.experiment_id,
            model_name=source.model_name,
            model_family=source.model_family,
            model_version=source.model_version,
            status=ForecastModelStatus.pending,
            hyperparameters_json={
                **source.hyperparameters_json,
                "max_steps": previous_steps + request.additional_steps,
                "resumed_from": source.id,
            },
            supports_groups=True,
            supports_trend=True,
            supports_seasonality=True,
            model_framework=source.model_framework,
            model_architecture=source.model_architecture,
            accelerator=source.accelerator,
            deterministic=source.deterministic,
            input_size=source.input_size,
            checkpoint_available=True,
            checkpoint_count=1,
            checkpoint_checksum=source.checkpoint_checksum,
            artifact_storage_key=source.artifact_storage_key,
            artifact_checksum=source.artifact_checksum,
            deep_model_status="resuming",
        )
        self.db.add(resumed)
        self.db.commit()
        resumed_directory = self._artifact_directory(source.experiment_id, resumed.id)
        resumed_checkpoint = resumed_directory / "checkpoints" / "latest"
        resumed_directory.mkdir(parents=True, exist_ok=False)
        started = time.perf_counter()
        try:
            loaded.fit(df=None, val_size=0, use_init_models=False, verbose=False)
            loaded.save(str(resumed_checkpoint), save_dataset=True, overwrite=False)
            checksum = NHiTSTrainer._directory_checksum(resumed_checkpoint)
            resumed.status = ForecastModelStatus.completed
            resumed.deep_model_status = "completed"
            resumed.training_duration_ms = int((time.perf_counter() - started) * 1000)
            resumed.completed_at = datetime.now(UTC)
            resumed.checkpoint_checksum = checksum
            resumed.artifact_checksum = checksum
            resumed.artifact_storage_key = str(
                resumed_checkpoint.relative_to(self.settings.forecast_artifact_root.resolve())
            ).replace("\\", "/")
            self.db.add(
                DeepForecastCheckpoint(
                    model_run_id=resumed.id,
                    checkpoint_type="latest",
                    global_step=previous_steps + request.additional_steps,
                    checksum=checksum,
                    file_size_bytes=sum(
                        file.stat().st_size for file in resumed_checkpoint.rglob("*") if file.is_file()
                    ),
                    framework_version=resumed.training_framework_version,
                )
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            failed = self.db.get(ForecastModelRun, resumed.id)
            if failed:
                failed.status = ForecastModelStatus.failed
                failed.deep_model_status = "failed"
                failed.failure_message = self._safe_failure(exc)
                self.db.commit()
            raise
        return DeepCheckpointResumeResponse(
            source_model_run_id=source.id,
            resumed_model_run_id=resumed.id,
            status="completed",
            restored_checkpoint_checksum=resumed.checkpoint_checksum or source.checkpoint_checksum,
            previous_steps=previous_steps,
            requested_additional_steps=request.additional_steps,
        )

    def _readiness(self, prepared_id: str, snapshot_id: str | None) -> DeepForecastReadinessSnapshot:
        statement = select(DeepForecastReadinessSnapshot).where(
            DeepForecastReadinessSnapshot.prepared_dataset_id == prepared_id
        )
        if snapshot_id:
            statement = statement.where(DeepForecastReadinessSnapshot.id == snapshot_id)
        else:
            statement = statement.order_by(DeepForecastReadinessSnapshot.created_at.desc())
        readiness = self.db.scalar(statement)
        if not readiness:
            raise FileNotFoundError("Deep readiness snapshot was not found")
        return readiness

    def _create_records(
        self, prepared: PreparedDataset, readiness: DeepForecastReadinessSnapshot, config: NHiTSConfig
    ) -> tuple[ForecastExperiment, ForecastModelRun]:
        version = (
            self.db.scalar(
                select(func.max(ForecastExperiment.experiment_version)).where(
                    ForecastExperiment.prepared_dataset_id == prepared.id
                )
            )
            or 0
        ) + 1
        configuration = config.model_dump(mode="json")
        configuration_hash = hashlib.sha256(json.dumps(configuration, sort_keys=True).encode()).hexdigest()
        splits = PreparationStorageService(self.settings).json_file(prepared.id, "splits")
        split_map = {item["name"]: item for item in splits["splits"]}  # type: ignore[index]
        experiment = ForecastExperiment(
            prepared_dataset_id=prepared.id,
            experiment_version=version,
            forecasting_engine_version="neuralforecast-3.1",
            status=ForecastExperimentStatus.training,
            target_column=prepared.target_column,
            date_column=prepared.date_column,
            group_columns_json=prepared.group_columns_json,
            frequency=prepared.frequency,
            forecast_horizon=config.forecast_horizon,
            selection_metric="mae",
            random_seed=config.random_seed,
            configuration_json=configuration,
            configuration_hash=configuration_hash,
            prepared_artifact_checksum=prepared.prepared_checksum,
            source_dataset_checksum=prepared.source_checksum,
            train_start=split_map["train"]["start"],
            train_end=split_map["train"]["end"],
            validation_start=split_map["validation"]["start"],
            validation_end=split_map["validation"]["end"],
            test_start=split_map["test"]["start"],
            test_end=split_map["test"]["end"],
            backtest_fold_count=0,
            experiment_family="deep_forecasting",
            deep_forecasting_enabled=True,
            deep_engine="neuralforecast",
            deep_data_config_json=readiness.report_json,
            deep_runtime_config_json={"accelerator": config.accelerator, "deterministic": config.deterministic},
            deep_readiness_status=readiness.readiness_status,
            metadata_json={"readiness_snapshot_id": readiness.id, "final_test_evaluated": False},
        )
        run = ForecastModelRun(
            experiment_id=experiment.id,
            model_name="nhits",
            model_family="deep_forecasting",
            model_version="3.1.9",
            status=ForecastModelStatus.fitting,
            hyperparameters_json=configuration,
            supports_groups=True,
            supports_trend=True,
            supports_seasonality=True,
            model_framework="neuralforecast",
            model_architecture="N-HiTS",
            deterministic=config.deterministic,
            input_size=config.input_size,
            training_framework_version="3.1.9",
            torch_version=self._torch_version(),
            deep_model_status="training",
        )
        experiment.model_runs.append(run)
        self.db.add(experiment)
        self.db.commit()
        return experiment, run

    def _frames(
        self, prepared: PreparedDataset, readiness: DeepForecastReadinessSnapshot
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame | None]:
        frame = pd.read_csv(PreparationStorageService(self.settings).artifact(prepared.id), low_memory=False)
        report = readiness.report_json
        time_column = str(report["time_column"])
        target = str(report["target_column"])
        groups = list(readiness.group_columns_json)
        if not groups:
            frame["__deep_single_series"] = "all"
            groups = ["__deep_single_series"]
        frame[time_column] = pd.to_datetime(frame[time_column], errors="raise")
        frame["unique_id"] = frame[groups].apply(lambda row: _series_id(tuple(row)), axis=1)
        selected = list(
            dict.fromkeys(
                [
                    *readiness.historical_covariates_json,
                    *readiness.future_covariates_json,
                    *readiness.static_covariates_json,
                ]
            )
        )
        for column in selected:
            if not pd.api.types.is_numeric_dtype(frame[column]):
                values = sorted(str(value) for value in frame[column].dropna().unique())
                mapping = {value: index for index, value in enumerate(values)}
                frame[column] = frame[column].astype("string").map(mapping)
            frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(frame[column].median())
        canonical = frame.rename(columns={time_column: "ds", target: "y"})
        splits = PreparationStorageService(self.settings).json_file(prepared.id, "splits")
        split_map = {item["name"]: item for item in splits["splits"]}  # type: ignore[index]
        train_end = pd.Timestamp(split_map["train"]["end"])
        validation_start = pd.Timestamp(split_map["validation"]["start"])
        validation_end = pd.Timestamp(split_map["validation"]["end"])
        temporal_columns = [
            "unique_id",
            "ds",
            "y",
            *readiness.historical_covariates_json,
            *readiness.future_covariates_json,
        ]
        train = canonical.loc[canonical["ds"] <= train_end, temporal_columns].sort_values(["unique_id", "ds"])
        train["y"] = train.groupby("unique_id", sort=False)["y"].ffill()
        training_medians = train.groupby("unique_id", sort=False)["y"].transform("median")
        train["y"] = train["y"].fillna(training_medians)
        if train["y"].isna().any():
            raise ValueError("Training target gaps cannot be resolved from training-only evidence")
        validation = canonical.loc[
            (canonical["ds"] >= validation_start) & (canonical["ds"] <= validation_end), temporal_columns
        ].sort_values(["unique_id", "ds"])
        static = (
            canonical[["unique_id", *readiness.static_covariates_json]].drop_duplicates("unique_id")
            if readiness.static_covariates_json
            else None
        )
        if validation.groupby("unique_id").size().min() < readiness.horizon:
            raise ValueError("Validation split does not cover the configured horizon")
        validation = validation.groupby("unique_id", sort=True).head(readiness.horizon)
        return train, validation, static

    def _artifact_directory(self, experiment_id: str, run_id: str) -> Path:
        uuid.UUID(experiment_id)
        uuid.UUID(run_id)
        root = self.settings.forecast_artifact_root.resolve()
        path = (root / "training" / experiment_id / run_id).resolve()
        if root not in path.parents:
            raise ValueError("Invalid training artifact path")
        return path

    def _write_artifacts(self, directory: Path, config: NHiTSConfig, result: Any, hardware: dict[str, object]) -> None:
        (directory / "logs").mkdir()
        (directory / "metrics").mkdir()
        (directory / "plots").mkdir()
        (directory / "training").mkdir()
        self._atomic(directory / "config.yaml", config.to_yaml())
        self._atomic(directory / "metrics" / "metrics.json", json.dumps(result.metrics, indent=2, sort_keys=True))
        self._atomic(
            directory / "training" / "summary.json",
            json.dumps(
                {
                    "training_duration_ms": result.training_duration_ms,
                    "parameter_count": result.parameter_count,
                    "hardware": hardware,
                    "git_commit": self._git_commit(),
                    "final_test_evaluated": False,
                },
                indent=2,
                sort_keys=True,
            ),
        )
        result.predictions.to_csv(directory / "metrics" / "validation_predictions.csv", index=False)
        with (directory / "training" / "history.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["step", "loss", "validation_loss", "duration_ms"])
            writer.writeheader()
            writer.writerows(result.history)
        self._plot_history(directory / "plots", result.history)
        self._atomic(directory / "logs" / "training.log", f"completed duration_ms={result.training_duration_ms}\n")

    @staticmethod
    def _plot_history(directory: Path, history: list[dict[str, object]]) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        steps: list[int] = []
        losses: list[float] = []
        for row in history:
            step = row.get("step")
            loss = row.get("loss")
            if isinstance(step, int) and isinstance(loss, int | float):
                steps.append(step)
                losses.append(float(loss))
        if not steps:
            steps = [0]
            losses = [float("nan")]
        figure, axis = plt.subplots()
        axis.plot(steps, losses, label="training loss")
        axis.set_xlabel("step")
        axis.set_ylabel("loss")
        axis.legend()
        figure.savefig(directory / "loss.png")
        figure.savefig(directory / "loss.svg")
        plt.close(figure)

    @staticmethod
    def _atomic(path: Path, content: str) -> None:
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)

    @staticmethod
    def _git_commit() -> str | None:
        try:
            return subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=2
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    @staticmethod
    def _torch_version() -> str:
        import torch

        return str(torch.__version__)

    @staticmethod
    def _safe_failure(exc: Exception) -> str:
        return (
            str(exc)[:500]
            if isinstance(exc, (ValueError, FileNotFoundError, RuntimeError))
            else "Deep training failed safely"
        )

    def _response(self, run: ForecastModelRun) -> DeepTrainingExperimentResponse:
        experiment = self.db.get(ForecastExperiment, run.experiment_id)
        metrics = (
            DeepTrainingMetrics.model_validate(run.validation_metrics_json) if run.validation_metrics_json else None
        )
        return DeepTrainingExperimentResponse(
            experiment_id=run.experiment_id,
            model_run_id=run.id,
            prepared_dataset_id=experiment.prepared_dataset_id if experiment else "",
            model_name=run.model_name,
            status=run.status.value,
            current_epoch=None,
            max_steps=int(run.hyperparameters_json.get("max_steps", 0)),
            selected_accelerator=run.accelerator or "pending",
            training_duration_ms=run.training_duration_ms,
            checkpoint_available=run.checkpoint_available,
            checkpoint_checksum=run.checkpoint_checksum,
            metrics=metrics,
            failure_message=run.failure_message,
            created_at=run.created_at,
            completed_at=run.completed_at,
        )
