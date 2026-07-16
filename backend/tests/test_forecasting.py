import math
from types import SimpleNamespace

import numpy as np
import pandas as pd

from app.core.config import Settings
from app.services.forecast_metrics import metric_set
from app.services.forecast_model_registry import forecast
from app.services.gradient_boosting_service import fit_predict, safe_gbm_features


def frame(values: list[float], start: str = "2024-01-01") -> pd.DataFrame:
    return pd.DataFrame(
        {"date": pd.date_range(start, periods=len(values)), "target": values, "group": "A", "trend": range(len(values))}
    )


def test_forecast_registry_endpoint(client) -> None:
    response = client.get("/api/v1/forecasting/models")
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} >= {"naive_last", "seasonal_naive", "ridge_regression"}
    assert {item["id"] for item in response.json()} >= {"lightgbm_regressor", "xgboost_regressor", "catboost_regressor"}


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


def test_gbm_safe_features_exclude_target_derived_and_holdout_lags() -> None:
    features = [
        SimpleNamespace(
            feature_name="revenue",
            included=True,
            leakage_risk="excluded_target",
            availability_type="target_derived",
            feature_type="target",
        ),
        SimpleNamespace(
            feature_name="roas",
            included=False,
            leakage_risk="target_derived",
            availability_type="target_derived",
            feature_type="derived_metric",
        ),
        SimpleNamespace(
            feature_name="revenue_lag_1",
            included=True,
            leakage_risk="none",
            availability_type="historical_only",
            feature_type="lag",
        ),
        SimpleNamespace(
            feature_name="calendar_week",
            included=True,
            leakage_risk="none",
            availability_type="known_in_advance",
            feature_type="calendar",
        ),
    ]
    allowed, excluded = safe_gbm_features(features, "revenue", ["group"])
    assert allowed == ["calendar_week", "group"]
    assert {"revenue", "roas", "revenue_lag_1"} <= set(excluded)


def test_all_gradient_boosting_models_fit_and_preserve_groups() -> None:
    train = frame([10 + i * 0.5 for i in range(40)])
    future = frame([30 + i * 0.5 for i in range(5)], "2024-02-10")
    params = {
        "n_estimators": 20,
        "max_depth": 3,
        "learning_rate": 0.1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.0,
        "reg_lambda": 1.0,
    }
    for model in ("lightgbm_regressor", "xgboost_regressor", "catboost_regressor"):
        predicted, artifact, _ = fit_predict(
            model, train, future, "target", ["trend", "group"], ["group"], params, Settings(), 5
        )
        assert len(predicted) == 5
        assert predicted["group"].tolist() == ["A"] * 5
        assert artifact["features"] == ["trend", "group"]
