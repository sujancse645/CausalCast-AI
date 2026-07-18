import hashlib
import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.deep_learning.config.nhits import NHiTSConfig
from app.deep_learning.models.nhits import NHiTSForecastModel
from app.deep_learning.utils.metrics import regression_metrics

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NHiTSTrainingResult:
    metrics: dict[str, float | None]
    predictions: pd.DataFrame
    training_duration_ms: int
    checkpoint_path: Path
    checkpoint_checksum: str
    parameter_count: int
    history: list[dict[str, object]]


class NHiTSTrainer:
    """Executes leakage-safe N-HiTS fitting and governed validation evaluation."""

    def __init__(self, model_factory: NHiTSForecastModel | None = None) -> None:
        self.model_factory = model_factory or NHiTSForecastModel()

    @staticmethod
    def seed(config: NHiTSConfig) -> None:
        import torch

        random.seed(config.random_seed)
        np.random.seed(config.random_seed)
        torch.manual_seed(config.random_seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(config.random_seed)
        if config.deterministic:
            torch.use_deterministic_algorithms(True, warn_only=True)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def train(
        self,
        *,
        config: NHiTSConfig,
        training_frame: pd.DataFrame,
        validation_frame: pd.DataFrame,
        static_frame: pd.DataFrame | None,
        historical_covariates: list[str],
        future_covariates: list[str],
        static_covariates: list[str],
        frequency: str,
        accelerator: str,
        artifact_directory: Path,
    ) -> NHiTSTrainingResult:
        from neuralforecast import NeuralForecast

        self.seed(config)
        artifact_directory.mkdir(parents=True, exist_ok=False)
        checkpoint_directory = artifact_directory / "checkpoints" / "latest"
        model = self.model_factory.build(
            config,
            historical_covariates,
            future_covariates,
            static_covariates,
            accelerator,
            str(artifact_directory / "framework"),
        )
        forecast = NeuralForecast(models=[model], freq=frequency)
        started = time.perf_counter()
        logger.info("Starting governed N-HiTS fit", extra={"rows": len(training_frame), "accelerator": accelerator})
        forecast.fit(df=training_frame, static_df=static_frame, val_size=0, verbose=False)
        future_frame = validation_frame.drop(columns=["y"], errors="ignore")
        predictions = forecast.predict(futr_df=future_frame if future_covariates else None)
        duration_ms = int((time.perf_counter() - started) * 1000)
        predicted_column = next(column for column in predictions if column not in {"unique_id", "ds"})
        merged = validation_frame[["unique_id", "ds", "y"]].merge(predictions, on=["unique_id", "ds"], how="inner")
        metrics = regression_metrics(merged["y"].tolist(), merged[predicted_column].tolist())
        forecast.save(str(checkpoint_directory), save_dataset=True, overwrite=False)
        checksum = self._directory_checksum(checkpoint_directory)
        parameter_count = sum(parameter.numel() for parameter in model.parameters())
        history = self._history(model, duration_ms)
        logger.info("Completed governed N-HiTS fit", extra={"duration_ms": duration_ms, "rows": len(merged)})
        return NHiTSTrainingResult(
            metrics=metrics,
            predictions=merged.rename(columns={predicted_column: "prediction"}),
            training_duration_ms=duration_ms,
            checkpoint_path=checkpoint_directory,
            checkpoint_checksum=checksum,
            parameter_count=parameter_count,
            history=history,
        )

    @staticmethod
    def _history(model: Any, duration_ms: int) -> list[dict[str, object]]:
        raw = getattr(model, "train_trajectories", {})
        steps = raw.get("step", []) if isinstance(raw, dict) else []
        losses = raw.get("train_loss", []) if isinstance(raw, dict) else []
        validation = raw.get("valid_loss", []) if isinstance(raw, dict) else []
        rows: list[dict[str, object]] = []
        for index, step in enumerate(steps):
            rows.append(
                {
                    "step": int(step),
                    "loss": float(losses[index]) if index < len(losses) else None,
                    "validation_loss": float(validation[index]) if index < len(validation) else None,
                    "duration_ms": duration_ms,
                }
            )
        return rows

    @staticmethod
    def _directory_checksum(path: Path) -> str:
        digest = hashlib.sha256()
        for file in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(str(file.relative_to(path)).replace("\\", "/").encode())
            with file.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def runtime_metadata() -> dict[str, object]:
        import neuralforecast
        import torch

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "python_hash_seed": os.environ.get("PYTHONHASHSEED"),
            "torch_version": torch.__version__,
            "neuralforecast_version": neuralforecast.__version__,
            "cuda_version": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
        }
