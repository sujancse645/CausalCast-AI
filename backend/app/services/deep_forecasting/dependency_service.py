from functools import lru_cache
from importlib import metadata, util

from packaging.version import InvalidVersion, Version

from app.schemas.deep_forecasting import DeepForecastDependencyResponse

PACKAGES: dict[str, tuple[str | None, str | None, bool, list[str]]] = {
    "torch": ("2.2", "2.8", False, ["nhits", "temporal_fusion_transformer", "nbeats"]),
    "neuralforecast": ("2.0", "3.1.99", False, ["nhits", "nbeats"]),
    "lightning": ("2.2", "2.5", False, ["nhits", "temporal_fusion_transformer", "nbeats"]),
    "numpy": ("1.26", "2.4", True, []),
    "pandas": ("2.2", "2.3", True, []),
    "scikit-learn": ("1.5", "1.9", True, []),
    "joblib": ("1.4", "1.5", True, []),
}
IMPORT_NAMES = {"scikit-learn": "sklearn"}


@lru_cache(maxsize=1)
def dependency_report() -> tuple[DeepForecastDependencyResponse, ...]:
    result: list[DeepForecastDependencyResponse] = []
    for package, (minimum, maximum, required, models) in PACKAGES.items():
        import_name = IMPORT_NAMES.get(package, package)
        installed = util.find_spec(import_name) is not None
        version: str | None = None
        error: str | None = None
        compatible = False
        if installed:
            try:
                version = metadata.version(package)
                parsed = Version(version)
                compatible = (minimum is None or parsed >= Version(minimum)) and (
                    maximum is None or parsed <= Version(maximum)
                )
            except metadata.PackageNotFoundError:
                error = "metadata_unavailable"
            except InvalidVersion:
                error = "invalid_version"
        else:
            error = "not_installed"
        result.append(
            DeepForecastDependencyResponse(
                package_name=package,
                installed=installed,
                version=version,
                minimum_supported_version=minimum,
                maximum_tested_version=maximum,
                compatible=compatible,
                import_error_category=error,
                required=required,
                optional=not required,
                models_affected=models,
            )
        )
    return tuple(result)


def package_available(name: str) -> bool:
    return any(item.package_name == name and item.installed and item.compatible for item in dependency_report())
