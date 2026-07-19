from typing import Any

from app.explainability.adapters.base import BaseExplainerAdapter
from app.explainability.core.engine import ExplainabilityEngine
from app.explainability.core.registry import ExplanationMethodRegistry


@ExplainabilityEngine.register_adapter("gradient_boosting")
class TreeExplainerAdapter(BaseExplainerAdapter):
    """
    Adapter for tree-based models like XGBoost, LightGBM, CatBoost.
    """

    def capabilities(self) -> dict[str, Any]:
        return {
            "supported": True,
            "reason": "supported",
            "methods": [
                ExplanationMethodRegistry.get_method("tree_shap_global"),
                ExplanationMethodRegistry.get_method("tree_shap_local"),
                ExplanationMethodRegistry.get_method("native_importance"),
                ExplanationMethodRegistry.get_method("permutation_importance"),
            ],
        }

    def explain_global(self, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if method == "native_importance":
            # Logic to extract native importance from stored artifact
            return {"type": "feature_importance", "data": [], "reliability_score": 1.0}
        elif method == "tree_shap_global":
            # Call gradient boosting service to get SHAP summary
            return {"type": "shap_summary", "data": [], "reliability_score": 0.9}
        elif method == "permutation_importance":
            return {"type": "permutation", "data": [], "reliability_score": 0.8}
        else:
            raise ValueError(f"Unsupported global method for trees: {method}")

    def explain_local(self, prediction_id: str, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        if method == "tree_shap_local":
            # Produce SHAP waterfall data
            return {"type": "shap_waterfall", "data": [], "reliability_score": 0.9}
        else:
            raise ValueError(f"Unsupported local method for trees: {method}")
