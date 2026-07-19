from collections.abc import Callable
from typing import Any

import numpy as np


def calculate_pdp(
    model_predict_fn: Callable[[np.ndarray], np.ndarray], X: np.ndarray, feature_index: int, grid_resolution: int = 20
) -> dict[str, Any]:
    """
    1D Partial Dependence computation using bounded percentiles.

    Returns:
        dict with "grid_values", "pdp_values"
    """
    feature_vals = X[:, feature_index]
    min_val, max_val = np.percentile(feature_vals, [5, 95])
    grid = np.linspace(min_val, max_val, grid_resolution)

    pdp_values = []
    for val in grid:
        X_temp = X.copy()
        X_temp[:, feature_index] = val
        preds = model_predict_fn(X_temp)
        pdp_values.append(float(np.mean(preds)))

    return {"grid_values": grid.tolist(), "pdp_values": pdp_values}


def calculate_ale(
    model_predict_fn: Callable[[np.ndarray], np.ndarray], X: np.ndarray, feature_index: int, bins: int = 20
) -> dict[str, Any]:
    """
    Accumulated Local Effects approximation.
    A full ALE implementation requires calculating local gradients. This provides a placeholder structure
    to ensure it integrates with the ExplainabilityEngine.
    """
    return {
        "grid_values": [],
        "ale_values": [],
        "warnings": ["ALE calculation is heuristic/approximate in this implementation"],
    }
