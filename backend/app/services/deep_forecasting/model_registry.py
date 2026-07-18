from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.deep_forecasting import DeepForecastModelDefinitionResponse
from app.services.deep_forecasting.dependency_service import package_available


@dataclass(frozen=True)
class Definition:
    identifier: str
    display_name: str
    family: str
    description: str
    dependency: str
    status: str
    enabled: bool
    static: bool
    quantiles: bool
    explainability: bool
    limitations: tuple[str, ...]
    future_phase: str


DEFINITIONS = (
    Definition(
        "nhits",
        "N-HiTS",
        "deep_hierarchical_interpolation",
        "Primary future deep multi-horizon forecasting architecture.",
        "neuralforecast",
        "training_ready",
        True,
        True,
        False,
        False,
        ("Training is not implemented in Phase 3C Part 1.", "Probabilistic losses are deferred."),
        "Phase 3C Part 2",
    ),
    Definition(
        "temporal_fusion_transformer",
        "Temporal Fusion Transformer",
        "attention_based_multi_horizon",
        "Optional attention-based grouped forecasting architecture.",
        "lightning",
        "planned",
        False,
        True,
        True,
        True,
        ("Optional and not implemented.", "CPU execution may be slow."),
        "Phase 3C Part 3 or later",
    ),
    Definition(
        "nbeats",
        "N-BEATS",
        "deep_residual_basis_expansion",
        "Optional fallback deep residual basis model.",
        "neuralforecast",
        "planned",
        False,
        False,
        False,
        False,
        ("Registry metadata only; no training adapter exists.",),
        "Phase 3C Part 2 or later",
    ),
)


def deep_models(settings: Settings) -> list[DeepForecastModelDefinitionResponse]:
    flags = {
        "nhits": settings.deep_forecasting_enable_nhits,
        "temporal_fusion_transformer": settings.deep_forecasting_enable_tft,
        "nbeats": settings.deep_forecasting_enable_nbeats,
    }
    result: list[DeepForecastModelDefinitionResponse] = []
    for item in DEFINITIONS:
        enabled = settings.deep_forecasting_enabled and flags[item.identifier]
        dependency_available = package_available(item.dependency) and package_available("torch")
        status = item.status if enabled or item.identifier == "nhits" else "planned"
        if not settings.deep_forecasting_enabled:
            status = "disabled"
        result.append(
            DeepForecastModelDefinitionResponse(
                identifier=item.identifier,
                display_name=item.display_name,
                family=item.family,
                description=item.description,
                implementation_status=status,
                enabled_by_default=item.enabled,
                dependency_name=item.dependency,
                dependency_available=dependency_available,
                supported_frequencies=["hourly", "daily", "weekly", "monthly"],
                supports_grouped_series=True,
                supports_global_model=True,
                supports_per_group_model=False,
                supports_historical_covariates=True,
                supports_future_covariates=True,
                supports_static_covariates=item.static,
                supports_quantiles=item.quantiles,
                supports_probabilistic_loss=item.quantiles,
                supports_gpu=True,
                supports_cpu=True,
                supports_checkpointing=True,
                supports_early_stopping=True,
                supports_explainability=item.explainability,
                minimum_history_formula="max(input_size + horizon, horizon * minimum_history_multiplier)",
                recommended_input_window="max(min_input_size, horizon * input_size_multiplier)",
                recommended_horizon="1..365 periods, governed by prepared split coverage",
                known_limitations=list(item.limitations),
                future_phase=item.future_phase,
            )
        )
    return result
