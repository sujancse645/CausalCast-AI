from typing import Any

def explain_drift(feature_name: str, p_value: float, effect_size: float, distribution_shift_type: str) -> dict[str, Any]:
    """
    Explain the nature of drift detected on a feature.
    """
    severity = "high" if p_value < 0.01 and effect_size > 0.5 else "medium" if p_value < 0.05 else "low"
    
    return {
        "feature": feature_name,
        "drift_severity": severity,
        "p_value": p_value,
        "effect_size": effect_size,
        "shift_type": distribution_shift_type,
        "recommended_action": "Consider retraining the model if this feature is highly important globally." if severity == "high" else "Monitor feature."
    }
