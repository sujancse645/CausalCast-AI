from abc import ABC, abstractmethod
from typing import Any

from app.models.explainability import Explanation
from app.models.forecasting import ForecastModelRun


class BaseExplainerAdapter(ABC):
    """
    Base class for model-specific explainers.
    """
    def __init__(self, model_run: ForecastModelRun):
        self.model_run = model_run

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """
        Return explainability capabilities of this model.
        e.g. {"native_importance": True, "shap_tree": False, "pdp": True}
        """
        pass

    @abstractmethod
    def explain_global(self, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Produce a global explanation (e.g. feature importance).
        """
        pass

    @abstractmethod
    def explain_local(self, prediction_id: str, method: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Produce a local explanation (e.g. SHAP waterfall) for a specific prediction.
        """
        pass
