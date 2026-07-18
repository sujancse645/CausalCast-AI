from typing import Any

from app.explainability.adapters.base import BaseExplainerAdapter
from app.explainability.core.engine import ExplainabilityEngine
from app.explainability.core.registry import ExplanationMethodRegistry
from app.models.forecasting import ForecastModelRun


@ExplainabilityEngine.register_adapter("attention_based_multi_horizon")
class TFTExplainerAdapter(BaseExplainerAdapter):
    """
    Adapter for Temporal Fusion Transformer.
    """

    def capabilities(self) -> dict[str, Any]:
        return {
            "supported": True,
            "reason": "planned_feature",
            "methods": [
                ExplanationMethodRegistry.get_method("tft_attention"),
                ExplanationMethodRegistry.get_method("tft_variable_selection"),
                ExplanationMethodRegistry.get_method("permutation_importance"),
            ]
        }

    def explain_global(self, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if method == "tft_variable_selection":
            return {"type": "feature_importance", "data": [], "reliability_score": 1.0}
        elif method == "permutation_importance":
            return {"type": "permutation", "data": [], "reliability_score": 0.8}
        else:
            raise ValueError(f"Unsupported global method for TFT: {method}")

    def explain_local(self, prediction_id: str, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if method == "tft_attention":
            return {"type": "attention", "data": [], "reliability_score": 1.0}
        else:
            raise ValueError(f"Unsupported local method for TFT: {method}")
