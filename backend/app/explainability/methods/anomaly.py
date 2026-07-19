from typing import Any


def explain_anomaly(anomaly_score: float, feature_contributions: dict[str, float]) -> dict[str, Any]:
    """
    Explain a specific anomaly based on the features that drove the anomaly score.
    """
    sorted_features = sorted(feature_contributions.items(), key=lambda x: abs(x[1]), reverse=True)
    return {
        "anomaly_score": anomaly_score,
        "top_contributing_features": [{"feature": k, "contribution": v} for k, v in sorted_features[:5]],
        "confidence": 0.85,
        "recommended_investigation": f"Investigate recent changes in {sorted_features[0][0]} if it is a leading indicator."
        if sorted_features
        else "No clear feature driver found.",
    }
