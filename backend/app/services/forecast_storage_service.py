import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.core.config import Settings


class ForecastStorageService:
    ALLOWED = {
        "model",
        "configuration",
        "metrics",
        "model_card",
        "environment",
        "validation_predictions",
        "backtest_predictions",
        "test_predictions",
        "residuals",
        "preprocessing",
        "feature_names",
        "hyperparameters",
        "tuning_trials",
        "feature_importance",
        "shap_summary",
    }

    def __init__(self, settings: Settings) -> None:
        self.root = settings.forecast_artifact_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _directory(self, experiment_id: str, model_run_id: str) -> Path:
        uuid.UUID(experiment_id)
        uuid.UUID(model_run_id)
        path = (self.root / "models" / experiment_id / model_run_id).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid forecast artifact path")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()

    def write_json(self, experiment_id: str, model_run_id: str, name: str, payload: object) -> tuple[str, str]:
        if name not in self.ALLOWED:
            raise ValueError("Unsupported artifact type")
        return self._atomic(
            experiment_id, model_run_id, name, ".json", json.dumps(payload, indent=2, default=str).encode()
        )

    def write_text(
        self, experiment_id: str, model_run_id: str, name: str, content: str, suffix: str
    ) -> tuple[str, str]:
        if name not in self.ALLOWED:
            raise ValueError("Unsupported artifact type")
        return self._atomic(experiment_id, model_run_id, name, suffix, content.encode())

    def write_frame(self, experiment_id: str, model_run_id: str, name: str, frame: pd.DataFrame) -> tuple[str, str]:
        return self.write_text(experiment_id, model_run_id, name, frame.to_csv(index=False), ".csv")

    def write_model(self, experiment_id: str, model_run_id: str, model: Any) -> tuple[str, str]:
        return self.write_joblib(experiment_id, model_run_id, "model", model)

    def write_joblib(self, experiment_id: str, model_run_id: str, name: str, model: Any) -> tuple[str, str]:
        if name not in self.ALLOWED:
            raise ValueError("Unsupported artifact type")
        directory = self._directory(experiment_id, model_run_id)
        temporary = directory / f".{name}.pkl.tmp"
        final = directory / f"{name}.pkl"
        joblib.dump(model, temporary)
        os.replace(temporary, final)
        return str(final.relative_to(self.root)).replace("\\", "/"), self.checksum(final)

    def _atomic(self, experiment_id: str, model_run_id: str, name: str, suffix: str, content: bytes) -> tuple[str, str]:
        directory = self._directory(experiment_id, model_run_id)
        final = directory / f"{name}{suffix}"
        temporary = directory / f".{name}{suffix}.tmp"
        temporary.write_bytes(content)
        os.replace(temporary, final)
        return str(final.relative_to(self.root)).replace("\\", "/"), self.checksum(final)

    def resolve(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if self.root not in path.parents or not path.is_file():
            raise FileNotFoundError("Forecast artifact is unavailable")
        return path

    def cleanup_experiment(self, experiment_id: str) -> None:
        uuid.UUID(experiment_id)
        path = (self.root / "models" / experiment_id).resolve()
        if self.root in path.parents:
            shutil.rmtree(path, ignore_errors=True)
