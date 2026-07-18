import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.dataset import Dataset, DatasetStatus
from app.models.forecasting import DeepForecastReadinessSnapshot
from app.models.preparation import PreparationReadiness, PreparationStatus, PreparedDataset
from app.schemas.deep_forecasting import (
    DeepForecastCovariateResponse,
    DeepForecastReadinessRequest,
    DeepForecastReadinessResponse,
    DeepForecastSequenceSummary,
    DeepForecastSeriesReadiness,
)
from app.services.deep_forecasting.dependency_service import dependency_report, package_available
from app.services.deep_forecasting.errors import DeepConfigurationError, DeepDatasetNotReadyError
from app.services.deep_forecasting.hardware_service import hardware_report
from app.services.deep_forecasting.storage import DeepForecastStorage
from app.services.preparation_storage_service import PreparationStorageService

FREQUENCY_ALIASES = {"hourly": "h", "daily": "D", "weekly": "7D", "monthly": "MS"}
TARGET_DERIVED_TERMS = (
    "roas",
    "average_order_value",
    "revenue_per_click",
    "revenue_per_impression",
    "campaign_success",
    "settlement",
)


def _file_checksum(path: Any) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _series_id(values: tuple[object, ...]) -> str:
    canonical = json.dumps([None if pd.isna(value) else str(value) for value in values], separators=(",", ":"))
    return "series_" + hashlib.sha256(canonical.encode()).hexdigest()[:24]


def resolve_input_size(horizon: int, available_history: int, settings: Settings, configured: int | None) -> int:
    value = configured or max(
        settings.deep_forecasting_min_input_size,
        horizon * settings.deep_forecasting_default_input_size_multiplier,
    )
    if value < settings.deep_forecasting_min_input_size or value > settings.deep_forecasting_max_input_size:
        raise DeepConfigurationError("Deep input size is outside configured limits")
    if value < horizon:
        raise DeepConfigurationError("Deep input size must be at least the forecast horizon")
    return value


def _classify(feature: Any, frame: pd.DataFrame, groups: list[str], target: str) -> DeepForecastCovariateResponse:
    name = str(feature.feature_name)
    lower = name.lower()
    target_derived = feature.availability_type == "target_derived" or any(
        term in lower for term in TARGET_DERIVED_TERMS
    )
    negative_lag = "lag_-" in lower or int(feature.parameters_json.get("lag", 0)) < 0
    centered = bool(feature.parameters_json.get("centered", False)) or "centered" in lower
    unsafe = (
        name == target
        or not feature.included
        or target_derived
        or feature.leakage_risk not in {"none", "review"}
        or negative_lag
        or centered
        or feature.feature_type in {"target", "date", "identifier", "text"}
    )
    category = "excluded"
    if not unsafe:
        if feature.availability_type == "known_in_advance":
            category = "future"
        elif feature.availability_type in {"historical_only", "observed_at_prediction_time"}:
            category = "historical"
        elif name in groups:
            category = "static"
        else:
            category = "historical"
    series_variability = False
    time_variability = False
    if name in frame:
        time_variability = bool(frame[name].nunique(dropna=False) > 1)
        if groups:
            series_variability = bool(frame.groupby(groups, dropna=False)[name].nunique(dropna=False).max() > 1)
    reason = None
    if unsafe:
        reason = (
            "target_column"
            if name == target
            else "target_derived"
            if target_derived
            else "negative_lag"
            if negative_lag
            else "centered_rolling"
            if centered
            else "excluded_or_unsafe_feature_metadata"
        )
    return DeepForecastCovariateResponse(
        name=name,
        source=",".join(feature.source_columns_json),
        category=category,
        data_type=feature.physical_type,
        known_at_forecast_time=category in {"future", "static"},
        target_derived=target_derived,
        leakage_status="blocked" if unsafe else "none",
        missing_rate=float(frame[name].isna().mean()) if name in frame else 1.0,
        cardinality=int(frame[name].nunique(dropna=True)) if name in frame else 0,
        series_variability=series_variability,
        time_variability=time_variability,
        approved_for_deep_forecasting=not unsafe,
        exclusion_reason=reason,
        future_coverage_status="not_applicable",
    )


def _requested_or_classified(
    requested: list[str] | None,
    classified: list[DeepForecastCovariateResponse],
    category: str,
) -> list[str]:
    available = {item.name for item in classified if item.category == category and item.approved_for_deep_forecasting}
    if requested is None:
        return sorted(available)
    unknown = set(requested) - available
    if unknown:
        raise DeepConfigurationError(
            f"Unsafe or incorrectly classified {category} covariates: {', '.join(sorted(unknown))}"
        )
    return list(dict.fromkeys(requested))


def analyze_readiness(
    db: Session,
    prepared_id: str,
    request: DeepForecastReadinessRequest,
    settings: Settings,
) -> DeepForecastReadinessResponse:
    try:
        uuid.UUID(prepared_id)
    except ValueError as exc:
        raise DeepDatasetNotReadyError("Prepared dataset identifier is invalid") from exc
    prepared = db.scalar(
        select(PreparedDataset).options(selectinload(PreparedDataset.features)).where(PreparedDataset.id == prepared_id)
    )
    if not prepared:
        raise DeepDatasetNotReadyError("Prepared dataset was not found")
    if prepared.status != PreparationStatus.completed or prepared.readiness_status != PreparationReadiness.model_ready:
        raise DeepDatasetNotReadyError("Prepared dataset must be completed and model-ready")
    source = db.get(Dataset, prepared.source_dataset_id)
    if not source or source.status == DatasetStatus.archived:
        raise DeepDatasetNotReadyError("Source dataset lineage is unavailable or archived")
    source_valid = source.checksum_sha256 == prepared.source_checksum
    storage = PreparationStorageService(settings)
    try:
        artifact = storage.artifact(prepared_id)
        manifest = storage.json_file(prepared_id, "manifest")
        splits_payload = storage.json_file(prepared_id, "splits")
        feature_catalog = storage.json_file(prepared_id, "feature_catalog")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise DeepDatasetNotReadyError("Required prepared manifests are unavailable") from exc
    checksum_valid = _file_checksum(artifact) == prepared.prepared_checksum
    if not checksum_valid or not source_valid:
        raise DeepDatasetNotReadyError("Prepared or source checksum validation failed")
    if not isinstance(manifest, dict) or not isinstance(splits_payload, dict) or not isinstance(feature_catalog, list):
        raise DeepDatasetNotReadyError("Prepared manifests are invalid")
    frame = pd.read_csv(artifact, low_memory=False)
    if len(frame) > settings.deep_forecasting_max_rows:
        raise DeepConfigurationError("Prepared dataset exceeds the deep row limit")
    target = request.target_column or prepared.target_column
    time_column = request.time_column or prepared.date_column
    groups = request.group_columns if request.group_columns is not None else prepared.group_columns_json
    required_columns = [target, time_column, *groups]
    missing_columns = [column for column in required_columns if column not in frame]
    if missing_columns:
        raise DeepConfigurationError("Required deep columns are missing")
    if len(set(required_columns)) != len(required_columns):
        raise DeepConfigurationError("Target, time, and group columns must be distinct")
    if len(prepared.features) > settings.deep_forecasting_max_features:
        raise DeepConfigurationError("Prepared feature count exceeds the deep feature limit")
    frame[time_column] = pd.to_datetime(frame[time_column], errors="coerce")
    numeric_target = pd.to_numeric(frame[target], errors="coerce")
    blockers: list[str] = []
    warnings: list[str] = []
    if frame[time_column].isna().any():
        blockers.append("Invalid timestamps remain in the prepared artifact.")
    if np.isinf(numeric_target.dropna()).any():
        blockers.append("Target contains infinite values.")
    frame[target] = numeric_target
    if request.target_transform == "log1p" and bool((numeric_target.dropna() < -1).any()):
        raise DeepConfigurationError("log1p target transform requires all targets to be at least -1")
    if not groups:
        frame["__deep_single_series"] = "all"
        groups = ["__deep_single_series"]
    if bool(frame[groups].isna().any(axis=None)):
        blockers.append("Group columns contain missing identifiers.")
    series_count = int(frame[groups].drop_duplicates().shape[0])
    if series_count > settings.deep_forecasting_max_series:
        raise DeepConfigurationError("Prepared series count exceeds the deep series limit")
    duplicates = int(frame.duplicated([*groups, time_column]).sum())
    if duplicates:
        blockers.append(f"Found {duplicates} duplicate series timestamps.")
    frame = frame.sort_values([*groups, time_column], kind="stable")
    frequency = prepared.frequency.lower()
    if frequency not in FREQUENCY_ALIASES:
        blockers.append(f"Unsupported prepared frequency: {prepared.frequency}.")
    expected = pd.Timedelta(hours=1) if frequency == "hourly" else pd.Timedelta(days=1 if frequency == "daily" else 7)
    irregular_series = 0
    if frequency != "monthly":
        for _, group_frame in frame.groupby(groups, dropna=False, sort=True):
            differences = group_frame[time_column].diff().dropna()
            if bool((differences != expected).any()):
                irregular_series += 1
    else:
        for _, group_frame in frame.groupby(groups, dropna=False, sort=True):
            periods = group_frame[time_column].dt.to_period("M")
            if bool(periods.duplicated().any()) or len(periods) > 1 and not periods.is_monotonic_increasing:
                irregular_series += 1
    if irregular_series:
        blockers.append(f"{irregular_series} series have irregular {frequency} frequency.")
    classified = [_classify(feature, frame, groups, target) for feature in prepared.features]
    historical = _requested_or_classified(request.historical_covariates, classified, "historical")
    future = _requested_or_classified(request.future_covariates, classified, "future")
    static = _requested_or_classified(request.static_covariates, classified, "static")
    if len(set(historical + future + static)) != len(historical + future + static):
        raise DeepConfigurationError("Covariate categories overlap")
    split_map = {item["name"]: item for item in splits_payload.get("splits", [])}
    if set(split_map) != {"train", "validation", "test"}:
        raise DeepDatasetNotReadyError("Chronological train, validation, and test splits are required")
    train_end = pd.Timestamp(split_map["train"]["end"])
    validation_start = pd.Timestamp(split_map["validation"]["start"])
    validation_end = pd.Timestamp(split_map["validation"]["end"])
    test_start = pd.Timestamp(split_map["test"]["start"])
    test_end = pd.Timestamp(split_map["test"]["end"])
    if not (train_end < validation_start <= validation_end < test_start <= test_end):
        raise DeepDatasetNotReadyError("Prepared splits overlap or are not chronological")
    train_frame = frame[frame[time_column] <= train_end]
    validation_frame = frame[(frame[time_column] >= validation_start) & (frame[time_column] <= validation_end)]
    test_frame = frame[(frame[time_column] >= test_start) & (frame[time_column] <= test_end)]
    max_train_history = int(train_frame.groupby(groups, dropna=False).size().max())
    input_size = resolve_input_size(request.horizon, max_train_history, settings, request.input_size)
    minimum_history = max(
        input_size + request.horizon, request.horizon * settings.deep_forecasting_min_history_multiplier
    )
    if request.horizon > settings.deep_forecasting_max_horizon:
        raise DeepConfigurationError("Requested horizon exceeds the deep limit")
    future_coverage_valid = True
    for covariate in future:
        for _, group_frame in validation_frame.groupby(groups, dropna=False, sort=True):
            horizon_values = group_frame.sort_values(time_column).head(request.horizon)[covariate]
            if len(horizon_values) < request.horizon or horizon_values.isna().any():
                future_coverage_valid = False
                blockers.append(f"Future covariate '{covariate}' does not cover the complete horizon for every series.")
                break
        for item in classified:
            if item.name == covariate:
                item.future_coverage_status = "complete" if future_coverage_valid else "missing"
    static_valid = True
    for covariate in static:
        if int(frame.groupby(groups, dropna=False)[covariate].nunique(dropna=False).max()) > 1:
            static_valid = False
            blockers.append(f"Configured static covariate '{covariate}' varies within a series.")
    series_reports: list[DeepForecastSeriesReadiness] = []
    mapping: dict[str, list[str | None]] = {}
    for key, group_frame in frame.groupby(groups, dropna=False, sort=True):
        values = key if isinstance(key, tuple) else (key,)
        identifier = _series_id(values)
        mapping[identifier] = [None if pd.isna(value) else str(value) for value in values]
        series_train = group_frame[group_frame[time_column] <= train_end]
        series_validation = group_frame[
            (group_frame[time_column] >= validation_start) & (group_frame[time_column] <= validation_end)
        ]
        series_test = group_frame[(group_frame[time_column] >= test_start) & (group_frame[time_column] <= test_end)]
        missing_targets = int(group_frame[target].isna().sum())
        reasons: list[str] = []
        if len(series_train) < minimum_history:
            reasons.append("insufficient_training_history")
        if missing_targets and not settings.deep_forecasting_allow_missing_targets:
            reasons.append("missing_targets")
        series_reports.append(
            DeepForecastSeriesReadiness(
                series_id=identifier,
                eligible=not reasons,
                observation_count=len(group_frame),
                required_observations=minimum_history,
                start=group_frame[time_column].min().date().isoformat(),
                end=group_frame[time_column].max().date().isoformat(),
                missing_target_count=missing_targets,
                training_windows=max(0, len(series_train) - input_size - request.horizon + 1),
                validation_windows=max(0, len(series_validation) - request.horizon + 1),
                test_windows=max(0, len(series_test) - request.horizon + 1),
                failure_reasons=reasons,
            )
        )
    eligible = sum(item.eligible for item in series_reports)
    missing_target_total = int(frame[target].isna().sum())
    if missing_target_total and not settings.deep_forecasting_allow_missing_targets:
        blockers.append(f"Target contains {missing_target_total} missing values across prepared splits.")
    if eligible != series_count:
        blockers.append(f"{series_count - eligible} series are ineligible; no series was silently dropped.")
    deep_dependencies = package_available("torch") and package_available("neuralforecast")
    if not deep_dependencies:
        warnings.append("Optional PyTorch and NeuralForecast training dependencies are not fully available.")
    hardware = hardware_report(settings, request.accelerator)
    status = (
        "disabled"
        if not settings.deep_forecasting_enabled
        else "blocked"
        if blockers
        else "dependency_missing"
        if not deep_dependencies
        else "ready_with_warnings"
        if warnings
        else "ready"
    )
    snapshot_id = str(uuid.uuid4())
    generated_at = datetime.now(UTC)
    sequence = DeepForecastSequenceSummary(
        input_size=input_size,
        horizon=request.horizon,
        step_size=1,
        minimum_history=minimum_history,
        total_training_windows=sum(item.training_windows for item in series_reports),
        total_validation_windows=sum(item.validation_windows for item in series_reports),
        total_test_windows=sum(item.test_windows for item in series_reports),
        expected_input_shape=[-1, input_size, 1 + len(historical) + len(future)],
        expected_output_shape=[-1, request.horizon, 1],
        validation_context_policy="Validation inputs may use train history; validation targets never enter inputs.",
        test_context_policy=(
            "After selection, test inputs may use train and validation history; test targets remain untouched."
        ),
    )
    response = DeepForecastReadinessResponse(
        snapshot_id=snapshot_id,
        prepared_dataset_id=prepared_id,
        readiness_status=status,
        preparation_status=prepared.status.value,
        model_ready=True,
        deep_forecasting_ready=status in {"ready", "ready_with_warnings"},
        checksum_valid=checksum_valid,
        source_checksum_valid=source_valid,
        manifest_valid=True,
        split_manifest_valid=True,
        feature_catalog_valid=True,
        frequency_valid=irregular_series == 0 and frequency in FREQUENCY_ALIASES,
        target_valid=not bool(np.isinf(numeric_target.dropna()).any()),
        group_valid=not bool(frame[groups].isna().any(axis=None)),
        future_covariates_valid=future_coverage_valid,
        static_covariates_valid=static_valid,
        sequence_windows_valid=all(item.training_windows > 0 for item in series_reports),
        minimum_history_valid=eligible == series_count,
        train_rows=len(train_frame),
        validation_rows=len(validation_frame),
        test_rows=len(test_frame),
        series_count=series_count,
        eligible_series_count=eligible,
        ineligible_series_count=series_count - eligible,
        feature_count=len(historical) + len(future) + len(static),
        historical_covariate_count=len(historical),
        future_covariate_count=len(future),
        static_covariate_count=len(static),
        target_column=target,
        time_column=time_column,
        frequency=frequency,
        input_size=input_size,
        horizon=request.horizon,
        covariates=classified,
        series=series_reports,
        sequence_summary=sequence,
        warnings=list(dict.fromkeys(warnings)),
        blockers=list(dict.fromkeys(blockers)),
        synthetic_data=bool(prepared.metadata_json.get("synthetic_data", False)),
        generated_at=generated_at,
        engine=settings.deep_forecasting_engine,
        selected_accelerator=hardware.selected_accelerator,
        dependency_status="available" if deep_dependencies else "missing_optional_dependencies",
        artifact_checksums={},
    )
    deep_storage = DeepForecastStorage(settings)
    artifact_payloads = {
        "runtime_config": {
            "engine": settings.deep_forecasting_engine,
            "random_seed": settings.deep_forecasting_random_seed,
            "deterministic": settings.deep_forecasting_deterministic,
            "accelerator": hardware.selected_accelerator,
        },
        "data_config": {
            "target": target,
            "time": time_column,
            "groups": groups,
            "frequency": frequency,
            "horizon": request.horizon,
            "input_size": input_size,
            "scaler": request.scaler_type,
            "scale_per_series": request.scale_per_series,
            "target_transform": request.target_transform,
        },
        "model_config": {"model_name": request.model_name, "implementation_status": "infrastructure_ready"},
        "covariate_catalog": [item.model_dump(mode="json") for item in classified],
        "leakage_report": {
            "excluded": [item.model_dump(mode="json") for item in classified if not item.approved_for_deep_forecasting],
            "blockers": response.blockers,
        },
        "sequence_manifest": sequence.model_dump(mode="json"),
        "hardware_report": hardware.model_dump(mode="json"),
        "dependencies": [item.model_dump(mode="json") for item in dependency_report()],
        "series_mapping": mapping,
    }
    manifests = [
        deep_storage.write_json(prepared_id, snapshot_id, name, payload) for name, payload in artifact_payloads.items()
    ]
    response.artifact_checksums = {str(item["logical_name"]): str(item["checksum"]) for item in manifests}
    readiness_manifest = deep_storage.write_json(
        prepared_id, snapshot_id, "readiness_report", response.model_dump(mode="json")
    )
    manifests.append(readiness_manifest)
    safe_manifest = [{key: value for key, value in item.items() if key != "storage_key"} for item in manifests]
    artifact_manifest = deep_storage.write_json(prepared_id, snapshot_id, "artifact_manifest", safe_manifest)
    response.artifact_checksums.update(
        readiness_report=str(readiness_manifest["checksum"]), artifact_manifest=str(artifact_manifest["checksum"])
    )
    report_payload = response.model_dump(mode="json")
    report_checksum = hashlib.sha256(json.dumps(report_payload, sort_keys=True).encode()).hexdigest()
    snapshot = DeepForecastReadinessSnapshot(
        id=snapshot_id,
        prepared_dataset_id=prepared_id,
        readiness_status=status,
        engine=settings.deep_forecasting_engine,
        model_name=request.model_name,
        target_column=target,
        time_column=time_column,
        group_columns_json=groups,
        horizon=request.horizon,
        input_size=input_size,
        series_count=series_count,
        eligible_series_count=eligible,
        historical_covariates_json=historical,
        future_covariates_json=future,
        static_covariates_json=static,
        warnings_json=response.warnings,
        blockers_json=response.blockers,
        report_json=report_payload,
        artifact_checksums_json=response.artifact_checksums,
        checksum=report_checksum,
    )
    db.add(snapshot)
    db.commit()
    return response


def latest_readiness(db: Session, prepared_id: str) -> DeepForecastReadinessResponse:
    snapshot = db.scalar(
        select(DeepForecastReadinessSnapshot)
        .where(DeepForecastReadinessSnapshot.prepared_dataset_id == prepared_id)
        .order_by(DeepForecastReadinessSnapshot.created_at.desc())
    )
    if not snapshot:
        raise DeepDatasetNotReadyError("Deep forecasting readiness has not been analyzed")
    return DeepForecastReadinessResponse.model_validate(snapshot.report_json)
