from typing import Any, Callable, Dict

class ExplanationMethodRegistry:
    """
    Central registry for explainability methods across all models.
    """
    _methods: Dict[str, dict[str, Any]] = {}

    @classmethod
    def register(cls, method_name: str, description: str, requires_background_data: bool = False, is_global: bool = True, is_local: bool = True):
        def decorator(func: Callable):
            cls._methods[method_name] = {
                "name": method_name,
                "description": description,
                "requires_background_data": requires_background_data,
                "is_global": is_global,
                "is_local": is_local,
                "callable": func
            }
            return func
        return decorator

    @classmethod
    def get_method(cls, method_name: str) -> dict[str, Any] | None:
        return cls._methods.get(method_name)

    @classmethod
    def get_all_methods(cls) -> Dict[str, dict[str, Any]]:
        return cls._methods
