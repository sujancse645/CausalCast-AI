from typing import Any

from app.explainability.adapters.base import BaseExplainerAdapter
from app.explainability.core.engine import ExplainabilityEngine
from app.explainability.core.registry import ExplanationMethodRegistry


@ExplainabilityEngine.register_adapter("classical")
class ClassicalExplainerAdapter(BaseExplainerAdapter):
    """
    Adapter for classical linear/statistical models (ARIMA, ETS, LinearRegression).
    """

    def capabilities(self) -> dict[str, Any]:
        return {
            "supported": True,
            "reason": "supported",
            "methods": [
                ExplanationMethodRegistry.get_method("linear_coefficients"),
                ExplanationMethodRegistry.get_method("permutation_importance"),
                ExplanationMethodRegistry.get_method("pdp"),
            ],
        }

    def explain_global(self, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if method == "linear_coefficients":
            return {"type": "coefficients", "data": [], "reliability_score": 1.0}
        elif method == "permutation_importance":
            return {"type": "permutation", "data": [], "reliability_score": 0.8}
        elif method == "pdp":
            return {"type": "pdp", "data": [], "reliability_score": 0.8}
        else:
            raise ValueError(f"Unsupported global method for classical: {method}")

    def explain_local(self, prediction_id: str, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        raise ValueError(f"Unsupported local method for classical: {method}")
