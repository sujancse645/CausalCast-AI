from typing import Any, Callable
import numpy as np

def generate_counterfactuals(
    model_predict_fn: Callable[[np.ndarray], np.ndarray],
    X_observation: np.ndarray,
    target_range: tuple[float, float],
    controllable_feature_indices: list[int],
    feature_bounds: dict[int, tuple[float, float]],
    max_iterations: int = 100
) -> list[dict[str, Any]]:
    """
    Generate counterfactual explanations using a simple random search/perturbation 
    within bounds for controllable features.
    """
    counterfactuals = []
    baseline_pred = float(model_predict_fn(X_observation.reshape(1, -1))[0])
    
    # We'll just generate random samples within bounds for controllable features
    # and see if they hit the target range.
    for i in range(max_iterations):
        X_cf = X_observation.copy()
        changes = {}
        for feat_idx in controllable_feature_indices:
            low, high = feature_bounds.get(feat_idx, (X_observation[feat_idx] * 0.5, X_observation[feat_idx] * 1.5))
            new_val = np.random.uniform(low, high)
            X_cf[feat_idx] = new_val
            changes[str(feat_idx)] = {"old": float(X_observation[feat_idx]), "new": float(new_val)}
            
        pred = float(model_predict_fn(X_cf.reshape(1, -1))[0])
        
        if target_range[0] <= pred <= target_range[1]:
            counterfactuals.append({
                "candidate_id": str(i),
                "baseline_prediction": baseline_pred,
                "counterfactual_prediction": pred,
                "changes": changes,
                "distance": float(np.linalg.norm(X_cf - X_observation))
            })
            
    # Sort by distance (cost)
    counterfactuals = sorted(counterfactuals, key=lambda x: x["distance"])
    return counterfactuals
