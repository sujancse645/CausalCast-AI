from typing import Any, Type

from app.explainability.adapters.base import BaseExplainerAdapter
from app.models.forecasting import ForecastModelRun


class ExplainabilityEngine:
    """
    Central engine routing explainability requests to the appropriate model-specific adapter.
    """
    _adapters: dict[str, Type[BaseExplainerAdapter]] = {}

    @classmethod
    def register_adapter(cls, model_family: str):
        """
        Decorator to register an adapter for a specific model family.
        """
        def decorator(adapter_cls: Type[BaseExplainerAdapter]):
            cls._adapters[model_family] = adapter_cls
            return adapter_cls
        return decorator

    @classmethod
    def get_adapter(cls, model_run: ForecastModelRun) -> BaseExplainerAdapter:
        """
        Instantiate the appropriate adapter for a given model run.
        """
        # Determine the key to use. Usually model_family (e.g. 'gradient_boosting', 'classical')
        adapter_cls = cls._adapters.get(model_run.model_family)
        if not adapter_cls:
            # Fallback to a generic black-box adapter if one is registered, otherwise raise error
            adapter_cls = cls._adapters.get("black_box")
            if not adapter_cls:
                raise ValueError(f"No explainability adapter registered for model family: {model_run.model_family}")
        
        return adapter_cls(model_run)

    @classmethod
    def get_capabilities(cls, model_run: ForecastModelRun) -> dict[str, Any]:
        """
        Return the discovered capabilities for this model.
        """
        try:
            adapter = cls.get_adapter(model_run)
            return adapter.capabilities()
        except ValueError:
            return {
                "supported": False,
                "reason": "unavailable_due_to_model_type",
                "methods": []
            }
