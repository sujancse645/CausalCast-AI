import math

import numpy as np


def metric_set(
    actual: list[float], predicted: list[float], insample: list[float], seasonal_period: int, epsilon: float
) -> dict[str, object]:
    a = np.asarray(actual, dtype=float)
    p = np.asarray(predicted, dtype=float)
    mask = np.isfinite(a) & np.isfinite(p)
    a = a[mask]
    p = p[mask]
    warnings: list[str] = []
    if not len(a):
        return {
            "row_count": 0,
            **{
                x: None for x in ("mae", "rmse", "wape", "smape", "mase", "bias", "mean_error", "median_absolute_error")
            },
            "warnings": ["No finite target/prediction pairs"],
        }
    error = p - a
    absolute = np.abs(error)
    denominator = float(np.abs(a).sum())
    wape = float(absolute.sum() / denominator) if denominator > epsilon else None
    if wape is None:
        warnings.append("WAPE undefined because absolute actual total is near zero")
    smape_terms = np.divide(
        2 * absolute, np.abs(a) + np.abs(p), out=np.zeros_like(a), where=(np.abs(a) + np.abs(p)) > epsilon
    )
    history = np.asarray([x for x in insample if math.isfinite(x)], dtype=float)
    lag = seasonal_period if len(history) > seasonal_period else 1
    scale = float(np.mean(np.abs(history[lag:] - history[:-lag]))) if len(history) > lag else 0.0
    mase = float(absolute.mean() / scale) if scale > epsilon else None
    if mase is None:
        warnings.append("MASE undefined because the in-sample naive scale is zero")
    return {
        "row_count": int(len(a)),
        "mae": float(absolute.mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "wape": wape,
        "smape": float(smape_terms.mean()),
        "mase": mase,
        "bias": float(error.mean()),
        "mean_error": float(error.mean()),
        "median_absolute_error": float(np.median(absolute)),
        "warnings": warnings,
    }


def residual_summary(actual: list[float], predicted: list[float]) -> dict[str, object]:
    residuals = np.asarray(predicted, dtype=float) - np.asarray(actual, dtype=float)
    threshold = 3 * float(np.std(residuals))
    autocorrelation = (
        float(np.corrcoef(residuals[:-1], residuals[1:])[0, 1])
        if len(residuals) > 2 and np.std(residuals[:-1]) and np.std(residuals[1:])
        else None
    )
    return {
        "mean": float(np.mean(residuals)),
        "standard_deviation": float(np.std(residuals)),
        "median": float(np.median(residuals)),
        "minimum": float(np.min(residuals)),
        "maximum": float(np.max(residuals)),
        "positive_ratio": float(np.mean(residuals > 0)),
        "autocorrelation_lag_1": autocorrelation,
        "large_residual_count": int(np.sum(np.abs(residuals) > threshold)) if threshold else 0,
    }
