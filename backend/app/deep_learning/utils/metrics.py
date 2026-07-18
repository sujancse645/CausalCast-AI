import numpy as np


def regression_metrics(actual: list[float], predicted: list[float], epsilon: float = 1e-8) -> dict[str, float | None]:
    """Compute deterministic metrics from executed finite prediction pairs."""

    observed = np.asarray(actual, dtype=float)
    forecast = np.asarray(predicted, dtype=float)
    finite = np.isfinite(observed) & np.isfinite(forecast)
    observed = observed[finite]
    forecast = forecast[finite]
    if not len(observed):
        return {name: None for name in ("mae", "rmse", "mape", "smape", "wape", "r2")}
    error = forecast - observed
    absolute = np.abs(error)
    nonzero = np.abs(observed) > epsilon
    mape = float(np.mean(absolute[nonzero] / np.abs(observed[nonzero]))) if nonzero.any() else None
    smape_denominator = np.abs(observed) + np.abs(forecast)
    smape = float(
        np.mean(
            np.divide(2 * absolute, smape_denominator, out=np.zeros_like(absolute), where=smape_denominator > epsilon)
        )
    )
    absolute_total = float(np.abs(observed).sum())
    centered_total = float(np.sum((observed - observed.mean()) ** 2))
    return {
        "mae": float(absolute.mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mape": mape,
        "smape": smape,
        "wape": float(absolute.sum() / absolute_total) if absolute_total > epsilon else None,
        "r2": float(1 - np.sum(error**2) / centered_total) if centered_total > epsilon else None,
    }
