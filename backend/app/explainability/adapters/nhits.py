from typing import Any

from app.explainability.adapters.base import BaseExplainerAdapter
from app.explainability.core.engine import ExplainabilityEngine
from app.explainability.core.registry import ExplanationMethodRegistry
from app.models.forecasting import ForecastModelRun


@ExplainabilityEngine.register_adapter("deep_hierarchical_interpolation")
class NHiTSExplainerAdapter(BaseExplainerAdapter):
    """
    Adapter for N-HiTS deep forecasting architecture.
    """

    def capabilities(self) -> dict[str, Any]:
        return {
            "supported": True,
            "reason": "supported",
            "methods": [
                ExplanationMethodRegistry.get_method("lag_occlusion_importance"),
                ExplanationMethodRegistry.get_method("permutation_importance"),
            ]
        }

    def explain_global(self, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if method == "lag_occlusion_importance":
            return {"type": "temporal_importance", "data": [], "reliability_score": 0.7, "warnings": ["Approximate method"]}
        elif method == "permutation_importance":
            return {"type": "permutation", "data": [], "reliability_score": 0.8}
        else:
            raise ValueError(f"Unsupported global method for N-HiTS: {method}")

    def explain_local(self, prediction_id: str, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        raise ValueError(f"Unsupported local method for N-HiTS: {method}")
