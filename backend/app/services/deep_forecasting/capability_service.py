from app.core.config import Settings
from app.schemas.deep_forecasting import (
    DeepForecastCapabilityResponse,
    DeepForecastLimitResponse,
)
from app.services.deep_forecasting.dependency_service import dependency_report
from app.services.deep_forecasting.hardware_service import hardware_report
from app.services.deep_forecasting.model_registry import deep_models


def configured_limits(settings: Settings) -> DeepForecastLimitResponse:
    return DeepForecastLimitResponse(
        max_rows=settings.deep_forecasting_max_rows,
        max_series=settings.deep_forecasting_max_series,
        max_features=settings.deep_forecasting_max_features,
        max_horizon=settings.deep_forecasting_max_horizon,
        max_history_rows_per_series=settings.deep_forecasting_max_history_rows_per_series,
        max_input_size=settings.deep_forecasting_max_input_size,
        minimum_history_multiplier=settings.deep_forecasting_min_history_multiplier,
    )


def capabilities(settings: Settings) -> DeepForecastCapabilityResponse:
    hardware = hardware_report(settings)
    return DeepForecastCapabilityResponse(
        enabled=settings.deep_forecasting_enabled,
        engine=settings.deep_forecasting_engine,
        infrastructure_status="ready" if settings.deep_forecasting_enabled else "disabled",
        selected_accelerator=hardware.selected_accelerator,
        models=deep_models(settings),
        dependencies=list(dependency_report()),
        hardware=hardware,
        limits=configured_limits(settings),
    )
