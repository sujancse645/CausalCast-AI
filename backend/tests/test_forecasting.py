import math

import numpy as np
import pandas as pd

from app.services.forecast_metrics import metric_set
from app.services.forecast_model_registry import forecast


def frame(values: list[float], start: str = "2024-01-01") -> pd.DataFrame:
    return pd.DataFrame(
        {"date": pd.date_range(start, periods=len(values)), "target": values, "group": "A", "trend": range(len(values))}
    )


def test_forecast_registry_endpoint(client) -> None:
    response = client.get("/api/v1/forecasting/models")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} >= {"naive_last", "seasonal_naive", "ridge_regression"}


def test_forecasting_stats_are_real_and_empty(client) -> None:
    response = client.get("/api/v1/forecasting/stats")
    assert response.status_code == 200
    assert response.json()["total_experiments"] == 0
    assert response.json()["average_test_wape"] is None


def test_naive_and_moving_average_use_history_only() -> None:
    train = frame([1, 2, 3, 4, 5, 6, 7])
    future = frame([100, 200], "2024-01-08")
    naive, _, _ = forecast("naive_last", train, future, "target", ["group"], "date", 7, 0, [])
    seasonal, _, _ = forecast("seasonal_naive", train, future, "target", ["group"], "date", 7, 0, [])
    average, _, _ = forecast("moving_average", train, future, "target", ["group"], "date", 7, 7, [])
    assert naive.prediction.tolist() == [7, 7]
    assert seasonal.prediction.tolist() == [1, 2]
    assert average.prediction.tolist() == [4, 4]


def test_drift_is_deterministic_and_group_is_preserved() -> None:
    predicted, _, _ = forecast(
        "drift", frame([2, 4, 6]), frame([0, 0], "2024-01-04"), "target", ["group"], "date", 7, 0, []
    )
    assert predicted.prediction.tolist() == [8, 10]
    assert predicted["group"].tolist() == ["A", "A"]


def test_statistical_and_linear_baselines_run() -> None:
    train = frame([10 + math.sin(i) + i * 0.1 for i in range(30)])
    future = frame([0] * 5, "2024-01-31")
    for model in ("simple_exponential_smoothing", "holt_linear", "holt_winters"):
        predicted, _, _ = forecast(model, train, future, "target", ["group"], "date", 7, 0, ["trend"])
        assert len(predicted) == 5 and np.isfinite(predicted.prediction).all()
    for model in ("linear_regression", "ridge_regression"):
        predicted, fitted, _ = forecast(model, train, future, "target", ["group"], "date", 7, 0, ["trend"])
        assert len(predicted) == 5 and fitted["features"] == ["trend", "group"]


def test_metrics_are_deterministic_and_safe() -> None:
    metrics = metric_set([1, 2, 3], [2, 2, 2], [1, 2, 3, 4], 1, 1e-8)
    assert metrics["mae"] == 2 / 3
    assert metrics["rmse"] == math.sqrt(2 / 3)
    assert metrics["wape"] == 2 / 6
    assert metrics["bias"] == 0
    zero = metric_set([0, 0], [1, 1], [5, 5], 1, 1e-8)
    assert zero["wape"] is None and zero["mase"] is None
