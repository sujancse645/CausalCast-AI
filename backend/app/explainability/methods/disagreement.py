from typing import Any

import numpy as np


def calculate_disagreement(preds_a: np.ndarray, preds_b: np.ndarray) -> dict[str, Any]:
    """
    Measures divergence between two models' predictions.
    """
    diff = preds_a - preds_b
    mean_abs_diff = float(np.mean(np.abs(diff)))
    max_diff = float(np.max(np.abs(diff)))

    # Correlation between predictions
    if len(preds_a) > 1 and np.std(preds_a) > 0 and np.std(preds_b) > 0:
        correlation = float(np.corrcoef(preds_a, preds_b)[0, 1])
    else:
        correlation = 1.0

    return {
        "mean_absolute_difference": mean_abs_diff,
        "max_difference": max_diff,
        "prediction_correlation": correlation,
        "disagreement_score": 1.0 - max(0.0, correlation),  # simplistic score
        "warnings": [],
    }
