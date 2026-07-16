from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing, Holt, SimpleExpSmoothing


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    name: str
    family: str
    description: str
    supports_groups: bool
    supports_trend: bool
    supports_seasonality: bool


DEFINITIONS = {
    "naive_last": ModelDefinition(
        "naive_last", "Last Value Naive", "naive", "Repeats the last observed value.", True, False, False
    ),
    "seasonal_naive": ModelDefinition(
        "seasonal_naive", "Seasonal Naive", "naive", "Repeats observations from one season earlier.", True, False, True
    ),
    "moving_average": ModelDefinition(
        "moving_average", "Moving Average", "statistical", "Repeats the trailing historical mean.", True, False, False
    ),
    "drift": ModelDefinition(
        "drift", "Drift", "statistical", "Extends the average first-to-last change.", True, True, False
    ),
    "simple_exponential_smoothing": ModelDefinition(
        "simple_exponential_smoothing",
        "Simple Exponential Smoothing",
        "statistical",
        "Exponentially weights recent observations.",
        True,
        False,
        False,
    ),
    "holt_linear": ModelDefinition(
        "holt_linear",
        "Holt Linear Trend",
        "statistical",
        "Exponential smoothing with a damped linear trend.",
        True,
        True,
        False,
    ),
    "holt_winters": ModelDefinition(
        "holt_winters", "Holt-Winters", "statistical", "Additive trend and seasonality baseline.", True, True, True
    ),
    "linear_regression": ModelDefinition(
        "linear_regression",
        "Linear Regression",
        "linear",
        "Linear baseline using governed known-in-advance features.",
        True,
        True,
        False,
    ),
    "ridge_regression": ModelDefinition(
        "ridge_regression",
        "Ridge Regression",
        "linear",
        "Regularized linear baseline using governed known-in-advance features.",
        True,
        True,
        False,
    ),
}


def _series_forecast(
    model: str, values: np.ndarray, steps: int, seasonal_period: int, window: int
) -> tuple[np.ndarray, Any]:
    values = values[np.isfinite(values)]
    if len(values) < 2:
        raise ValueError("Insufficient group history")
    if model == "naive_last":
        return np.repeat(values[-1], steps), {"last": float(values[-1])}
    if model == "seasonal_naive":
        if len(values) < seasonal_period:
            raise ValueError("Insufficient seasonal history")
        return np.resize(values[-seasonal_period:], steps), {"season": values[-seasonal_period:].tolist()}
    if model == "moving_average":
        if len(values) < window:
            raise ValueError(f"Insufficient history for moving average {window}")
        return np.repeat(np.mean(values[-window:]), steps), {"window": window, "mean": float(np.mean(values[-window:]))}
    if model == "drift":
        slope = (values[-1] - values[0]) / (len(values) - 1)
        return values[-1] + slope * np.arange(1, steps + 1), {"slope": float(slope)}
    if model == "simple_exponential_smoothing":
        fitted = SimpleExpSmoothing(values, initialization_method="estimated").fit(optimized=True)
    elif model == "holt_linear":
        fitted = Holt(values, damped_trend=True, initialization_method="estimated").fit(optimized=True)
    elif model == "holt_winters":
        if len(values) < 2 * seasonal_period:
            raise ValueError("Insufficient history for two seasonal cycles")
        fitted = ExponentialSmoothing(
            values, trend="add", seasonal="add", seasonal_periods=seasonal_period, initialization_method="estimated"
        ).fit(optimized=True)
    else:
        raise ValueError(f"Unsupported model {model}")
    return np.asarray(fitted.forecast(steps), dtype=float), fitted


def forecast(
    model: str,
    train: pd.DataFrame,
    future: pd.DataFrame,
    target: str,
    groups: list[str],
    date: str,
    seasonal_period: int,
    window: int,
    features: list[str],
) -> tuple[pd.DataFrame, Any, list[str]]:
    keys = groups or ["__all_group"]
    training = train.copy()
    predicting = future.copy()
    if not groups:
        training["__all_group"] = "all"
        predicting["__all_group"] = "all"
    outputs: list[pd.DataFrame] = []
    fitted_objects: dict[str, Any] = {}
    skipped: list[str] = []
    if model in {"linear_regression", "ridge_regression"}:
        usable = [x for x in features if x in training.columns and x in predicting.columns]
        if groups:
            usable = list(dict.fromkeys([*usable, *groups]))
        if not usable:
            raise ValueError("No safe linear features are available")
        numeric = [x for x in usable if pd.api.types.is_numeric_dtype(training[x])]
        categorical = [x for x in usable if x not in numeric]
        transformers: list[tuple[str, Any, list[str]]] = []
        if numeric:
            transformers.append(
                (
                    "numeric",
                    Pipeline(
                        [
                            ("impute", SimpleImputer(strategy="median")),
                            ("scale", StandardScaler() if model == "ridge_regression" else "passthrough"),
                        ]
                    ),
                    numeric,
                )
            )
        if categorical:
            transformers.append(
                (
                    "categorical",
                    Pipeline(
                        [
                            ("impute", SimpleImputer(strategy="most_frequent")),
                            ("encode", OneHotEncoder(handle_unknown="ignore", max_categories=100)),
                        ]
                    ),
                    categorical,
                )
            )
        estimator = Ridge(alpha=1.0) if model == "ridge_regression" else LinearRegression()
        pipeline = Pipeline([("preprocess", ColumnTransformer(transformers)), ("model", estimator)])
        valid = training[target].notna()
        pipeline.fit(training.loc[valid, usable], training.loc[valid, target])
        result = predicting.copy()
        result["prediction"] = pipeline.predict(predicting[usable])
        result["group"] = predicting[keys].astype(str).agg(" | ".join, axis=1)
        return result, {"pipeline": pipeline, "features": usable}, skipped
    for group_key, future_group in predicting.groupby(keys, sort=True):
        key_tuple = group_key if isinstance(group_key, tuple) else (group_key,)
        mask = pd.Series(True, index=training.index)
        for column, value in zip(keys, key_tuple, strict=True):
            mask &= training[column].eq(value)
        history = training.loc[mask].sort_values(date)[target].to_numpy(dtype=float)
        label = " | ".join(map(str, key_tuple))
        try:
            prediction, fitted = _series_forecast(model, history, len(future_group), seasonal_period, window)
            result = future_group.sort_values(date).copy()
            result["prediction"] = prediction
            result["group"] = label
            outputs.append(result)
            fitted_objects[label] = fitted
        except ValueError as exc:
            skipped.append(f"{label}: {exc}")
    if not outputs:
        raise ValueError("All groups were skipped: " + "; ".join(skipped))
    return pd.concat(outputs).sort_values([date, *groups]), fitted_objects, skipped
