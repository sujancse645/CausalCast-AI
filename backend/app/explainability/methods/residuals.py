import numpy as np
from typing import Any

def calculate_residuals(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    return y_true - y_pred

def residual_diagnostics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    """
    Computes distribution, bias, and autocorrelation of residuals.
    """
    res = calculate_residuals(y_true, y_pred)
    
    mean_res = float(np.mean(res))
    std_res = float(np.std(res))
    mae = float(np.mean(np.abs(res)))
    
    # Skewness heuristic
    n = len(res)
    skewness = float(np.sum((res - mean_res)**3) / (n * std_res**3)) if std_res > 0 else 0.0
    
    # Lag-1 Autocorrelation heuristic
    if n > 1 and std_res > 0:
        autocorr_1 = float(np.sum((res[:-1] - mean_res) * (res[1:] - mean_res)) / ( (n-1) * std_res**2 ))
    else:
        autocorr_1 = 0.0
        
    return {
        "mean_residual": mean_res,
        "std_residual": std_res,
        "mae": mae,
        "skewness": skewness,
        "autocorrelation_lag1": autocorr_1,
        "bias": "over_predicting" if mean_res < 0 else "under_predicting" if mean_res > 0 else "neutral",
        "warnings": []
    }
