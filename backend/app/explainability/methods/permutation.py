import numpy as np
from typing import Any, Callable

def calculate_permutation_importance(
    model_predict_fn: Callable[[Any], np.ndarray],
    X: np.ndarray,
    y: np.ndarray,
    metric_fn: Callable[[np.ndarray, np.ndarray], float],
    feature_names: list[str],
    n_repeats: int = 5,
    random_state: int = 42
) -> dict[str, Any]:
    """
    Time-series safe block permutation importance.
    For standard permutation, we shuffle the values of a feature, make predictions, and measure the drop in metric.
    
    Returns:
        dict with "importances", "importances_mean", "importances_std", etc.
    """
    rng = np.random.default_rng(random_state)
    baseline_pred = model_predict_fn(X)
    baseline_score = metric_fn(y, baseline_pred)
    
    importances = []
    
    for col_idx, feat_name in enumerate(feature_names):
        scores = []
        for _ in range(n_repeats):
            X_permuted = X.copy()
            # Time-series safe block permutation could be more complex (e.g. shuffling blocks of time)
            # For this simple implementation, we just shuffle the column
            # In a real TS scenario, we might shuffle segments/entities instead.
            rng.shuffle(X_permuted[:, col_idx])
            permuted_pred = model_predict_fn(X_permuted)
            score = metric_fn(y, permuted_pred)
            # Assuming higher score is better (e.g. R2) or lower is better (e.g. RMSE).
            # The caller must provide a metric_fn that aligns with this (e.g. negate RMSE).
            drop = baseline_score - score
            scores.append(drop)
        
        importances.append({
            "feature": feat_name,
            "mean_decrease": float(np.mean(scores)),
            "std_decrease": float(np.std(scores))
        })
        
    # Sort by mean decrease descending
    importances = sorted(importances, key=lambda x: x["mean_decrease"], reverse=True)
    
    return {
        "baseline_score": baseline_score,
        "importances": importances
    }
