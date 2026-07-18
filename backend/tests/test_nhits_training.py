from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from app.deep_learning.config.nhits import NHiTSConfig
from app.deep_learning.trainers.nhits import NHiTSTrainer
from app.deep_learning.utils.metrics import regression_metrics


def test_nhits_configuration_yaml_round_trip(tmp_path: Path) -> None:
    config = NHiTSConfig(forecast_horizon=2, input_size=4, max_steps=1, hidden_size=8)
    path = tmp_path / "nhits.yaml"
    path.write_text(config.to_yaml(), encoding="utf-8")
    assert NHiTSConfig.from_yaml(path) == config
    with pytest.raises(ValidationError):
        NHiTSConfig(forecast_horizon=5, input_size=4)


def test_deep_regression_metrics_are_executed_values() -> None:
    metrics = regression_metrics([1, 2, 3], [1, 3, 2])
    assert metrics["mae"] == pytest.approx(2 / 3)
    assert metrics["rmse"] == pytest.approx(np.sqrt(2 / 3))
    assert metrics["wape"] == pytest.approx(1 / 3)
    assert metrics["r2"] == pytest.approx(0)


def test_nhits_trainer_executes_and_saves_loadable_checkpoint(tmp_path: Path) -> None:
    pytest.importorskip("neuralforecast")
    dates = pd.date_range("2026-01-01", periods=14, freq="D")
    training = pd.DataFrame(
        {
            "unique_id": ["series-a"] * 12,
            "ds": dates[:12],
            "y": np.linspace(1, 12, 12),
        }
    )
    validation = pd.DataFrame({"unique_id": ["series-a"] * 2, "ds": dates[12:], "y": [13.0, 14.0]})
    result = NHiTSTrainer().train(
        config=NHiTSConfig(
            forecast_horizon=2,
            input_size=4,
            max_steps=1,
            hidden_size=8,
            hidden_layers=1,
            stack_count=1,
            batch_size=1,
            windows_batch_size=8,
            validation_check_steps=1,
            accelerator="cpu",
        ),
        training_frame=training,
        validation_frame=validation,
        static_frame=None,
        historical_covariates=[],
        future_covariates=[],
        static_covariates=[],
        frequency="D",
        accelerator="cpu",
        artifact_directory=tmp_path / "run",
    )
    assert result.metrics["mae"] is not None
    assert result.checkpoint_path.is_dir()
    assert len(result.checkpoint_checksum) == 64
    assert len(result.predictions) == 2
    from neuralforecast import NeuralForecast

    assert NeuralForecast.load(str(result.checkpoint_path)).models


def test_nhits_training_api_rejects_unknown_preparation(client) -> None:
    response = client.post(
        "/api/v1/deep/train/nhits",
        json={
            "prepared_dataset_id": "00000000-0000-4000-8000-000000000001",
            "configuration": {"forecast_horizon": 2, "input_size": 4},
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Prepared dataset was not found"
