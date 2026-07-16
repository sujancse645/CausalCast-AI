import hashlib
import json
import math
import platform
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
import statsmodels
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.dataset import Dataset
from app.models.forecasting import (
    ForecastEvaluation,
    ForecastExperiment,
    ForecastExperimentStatus,
    ForecastModelRun,
    ForecastModelStatus,
    ForecastPredictionArtifact,
    ForecastTuningTrial,
)
from app.models.preparation import PreparationReadiness, PreparationStatus, PreparedDataset
from app.schemas.forecasting import (
    FeatureImportanceResponse,
    ForecastComparisonResponse,
    ForecastExperimentConfig,
    ForecastExperimentHistoryResponse,
    ForecastExperimentResponse,
    ForecastExperimentSummary,
    ForecastMetricSet,
    ForecastModelDefinition,
    ForecastModelRunResponse,
    ForecastModelRunSummary,
    ForecastPredictionListResponse,
    ForecastPredictionRow,
    ForecastStatsResponse,
    GradientBoostingStatsResponse,
    ResidualSummary,
    ShapExplanationResponse,
    TuningSummaryResponse,
    TuningTrialSummary,
)
from app.services.forecast_metrics import metric_set, residual_summary
from app.services.forecast_model_registry import DEFINITIONS, dependency_info, forecast
from app.services.forecast_storage_service import ForecastStorageService
from app.services.gradient_boosting_service import GBM_MODELS, explanations, fit_predict, safe_gbm_features, tune
from app.services.preparation_storage_service import PreparationStorageService


class PreparedDatasetNotReadyForForecastingError(ValueError):
    pass


class ForecastArtifactMissingError(ValueError):
    pass


class ForecastChecksumMismatchError(ValueError):
    pass


class ForecastConfigurationError(ValueError):
    pass


class InsufficientForecastHistoryError(ValueError):
    pass


class UnsupportedForecastModelError(ValueError):
    pass


class ForecastTrainingError(RuntimeError):
    pass


class ForecastEvaluationError(RuntimeError):
    pass


class FinalTestAlreadyEvaluatedError(ValueError):
    pass


class ForecastExperimentNotFoundError(LookupError):
    pass


class ForecastModelRunNotFoundError(LookupError):
    pass


def _hash(path: Path) -> str:
    return ForecastStorageService.checksum(path)


def _response(item: ForecastExperiment) -> ForecastExperimentResponse:
    return ForecastExperimentResponse(
        id=item.id,
        prepared_dataset_id=item.prepared_dataset_id,
        experiment_version=item.experiment_version,
        status=item.status.value,
        target_column=item.target_column,
        frequency=item.frequency,
        selected_model_run_id=item.selected_model_run_id,
        created_at=item.created_at,
        completed_at=item.completed_at,
        forecasting_engine_version=item.forecasting_engine_version,
        date_column=item.date_column,
        group_columns=item.group_columns_json,
        forecast_horizon=item.forecast_horizon,
        selection_metric=item.selection_metric,
        random_seed=item.random_seed,
        configuration=item.configuration_json,
        prepared_artifact_checksum=item.prepared_artifact_checksum,
        source_dataset_checksum=item.source_dataset_checksum,
        train_start=item.train_start,
        train_end=item.train_end,
        validation_start=item.validation_start,
        validation_end=item.validation_end,
        test_start=item.test_start,
        test_end=item.test_end,
        backtest_fold_count=item.backtest_fold_count,
        validation_completed_at=item.validation_completed_at,
        test_evaluated_at=item.test_evaluated_at,
        failure_message=item.failure_message,
        metadata=item.metadata_json,
    )


def _summary(item: ForecastModelRun) -> ForecastModelRunSummary:
    return ForecastModelRunSummary(
        id=item.id,
        experiment_id=item.experiment_id,
        model_name=item.model_name,
        model_family=item.model_family,
        status=item.status.value,
        rank=item.rank,
        selection_score=item.selection_score,
        selected=item.selected,
        validation_metrics=ForecastMetricSet.model_validate(item.validation_metrics_json)
        if item.validation_metrics_json
        else None,
        backtest_metrics=ForecastMetricSet.model_validate(item.aggregate_backtest_metrics_json)
        if item.aggregate_backtest_metrics_json
        else None,
        training_duration_ms=item.training_duration_ms,
        backtest_duration_ms=item.backtest_duration_ms,
        failure_message=item.failure_message,
        tuning_method=item.tuning_method,
        tuning_trial_count=item.tuning_trial_count,
        failed_trial_count=item.failed_trial_count,
        tuning_duration_ms=item.tuning_duration_ms,
        best_iteration=item.best_iteration,
        best_score=item.best_score,
        feature_count=item.feature_count,
        strategy=item.strategy,
        explanation_available=item.explanation_available,
        dependency_version=item.dependency_version,
        global_model=item.global_model,
    )


def model_registry(settings: Settings) -> list[ForecastModelDefinition]:
    result: list[ForecastModelDefinition] = []
    for key, definition in DEFINITIONS.items():
        available, dependency_version = dependency_info(key)
        enabled = (
            settings.forecast_enable_ets or key not in {"simple_exponential_smoothing", "holt_linear", "holt_winters"}
        ) and (settings.forecast_enable_linear_baselines or key not in {"linear_regression", "ridge_regression"})
        enabled = (
            enabled
            and available
            and {
                "lightgbm_regressor": settings.gbm_enable_lightgbm,
                "xgboost_regressor": settings.gbm_enable_xgboost,
                "catboost_regressor": settings.gbm_enable_catboost,
            }.get(key, True)
        )
        result.append(
            ForecastModelDefinition(
                id=definition.id,
                name=definition.name,
                family=definition.family,
                description=definition.description,
                supports_groups=definition.supports_groups,
                supports_trend=definition.supports_trend,
                supports_seasonality=definition.supports_seasonality,
                enabled=enabled,
                supported_feature_types=["numeric", "categorical"] if key in GBM_MODELS else [],
                categorical_support=definition.categorical_support,
                tuning_support=definition.tuning_support,
                early_stopping_support=definition.early_stopping_support,
                explanation_support=definition.explanation_support,
                dependency_available=available,
                dependency_version=dependency_version,
                default_parameters=definition.default_parameters or {},
            )
        )
    return result


def _validate(
    db: Session, prepared_id: str, config: ForecastExperimentConfig, settings: Settings
) -> tuple[PreparedDataset, Dataset, pd.DataFrame, dict[str, Any], list[dict[str, Any]], list[str]]:
    prepared = db.scalar(
        select(PreparedDataset).options(selectinload(PreparedDataset.features)).where(PreparedDataset.id == prepared_id)
    )
    if (
        not prepared
        or prepared.status != PreparationStatus.completed
        or prepared.readiness_status != PreparationReadiness.model_ready
    ):
        raise PreparedDatasetNotReadyForForecastingError("Prepared dataset must be completed and model-ready")
    dataset = db.get(Dataset, prepared.source_dataset_id)
    if not dataset or dataset.checksum_sha256 != prepared.source_checksum:
        raise ForecastChecksumMismatchError("Source dataset checksum does not match preparation lineage")
    storage = PreparationStorageService(settings)
    try:
        path = storage.artifact(prepared_id)
        splits_payload = storage.json_file(prepared_id, "splits")
    except FileNotFoundError as exc:
        raise ForecastArtifactMissingError("Prepared artifact or split manifest is unavailable") from exc
    if _hash(path) != prepared.prepared_checksum:
        raise ForecastChecksumMismatchError("Prepared artifact checksum does not match persisted metadata")
    if not isinstance(splits_payload, dict):
        raise ForecastConfigurationError("Invalid split manifest")
    splits = splits_payload.get("splits", [])
    folds = splits_payload.get("backtest_folds", [])
    if len(splits) != 3 or not folds:
        raise ForecastConfigurationError("Train, validation, test, and backtest folds are required")
    split_map = {x["name"]: x for x in splits}
    required = {"train", "validation", "test"}
    if set(split_map) != required or not (
        split_map["train"]["end"]
        < split_map["validation"]["start"]
        <= split_map["validation"]["end"]
        < split_map["test"]["start"]
    ):
        raise ForecastConfigurationError("Chronological splits overlap or are invalid")
    frame = pd.read_csv(path, low_memory=False)
    target = config.target_column or prepared.target_column
    if target not in frame or prepared.date_column not in frame:
        raise ForecastConfigurationError("Prepared target or date column is missing")
    frame[prepared.date_column] = pd.to_datetime(frame[prepared.date_column], errors="coerce")
    frame[target] = pd.to_numeric(frame[target], errors="coerce")
    if frame[prepared.date_column].isna().any() or frame[target].notna().sum() == 0:
        raise ForecastConfigurationError("Prepared date or target values are invalid")
    group_count = frame[prepared.group_columns_json].drop_duplicates().shape[0] if prepared.group_columns_json else 1
    if group_count > settings.forecast_max_groups:
        raise ForecastConfigurationError("Prepared group count exceeds the configured limit")
    for name, minimum in (
        ("train", settings.forecast_min_train_periods),
        ("validation", settings.forecast_min_validation_periods),
        ("test", settings.forecast_min_test_periods),
    ):
        if int(split_map[name]["rows"]) < minimum:
            raise InsufficientForecastHistoryError(f"{name.title()} split has insufficient history")
    unsafe = [
        x.feature_name
        for x in prepared.features
        if x.included and x.feature_name != target and x.leakage_risk not in {"none", "review"}
    ]
    if unsafe:
        raise ForecastConfigurationError("Unsafe included features detected: " + ", ".join(unsafe))
    safe_features = [
        x.feature_name
        for x in prepared.features
        if x.included
        and x.feature_name != target
        and x.availability_type == "known_in_advance"
        and x.leakage_risk == "none"
    ]
    if config.linear_feature_allowlist is not None:
        rejected = set(config.linear_feature_allowlist) - set(safe_features)
        if rejected:
            raise ForecastConfigurationError("Linear feature allowlist contains unsafe or unavailable features")
        safe_features = config.linear_feature_allowlist
    return prepared, dataset, frame, split_map, folds, safe_features


def _slice(frame: pd.DataFrame, date: str, start: str, end: str) -> pd.DataFrame:
    return frame[(frame[date] >= pd.Timestamp(start)) & (frame[date] <= pd.Timestamp(end))].copy()


def _prediction_frame(predicted: pd.DataFrame, date: str, target: str, split: str, fold: int | None) -> pd.DataFrame:
    result = pd.DataFrame(
        {
            "date": predicted[date].dt.strftime("%Y-%m-%d"),
            "actual": predicted[target],
            "prediction": predicted["prediction"],
            "group": predicted["group"],
            "split": split,
            "fold": fold,
        }
    )
    result["residual"] = result["prediction"] - result["actual"]
    return result.dropna(subset=["actual", "prediction"])


def _add_evaluation(
    db: Session,
    run: ForecastModelRun,
    evaluation_type: str,
    split: str,
    fold: int | None,
    metrics: dict[str, object],
    horizon: int,
) -> None:
    db.add(
        ForecastEvaluation(
            model_run_id=run.id,
            evaluation_type=evaluation_type,
            split_name=split,
            fold_number=fold,
            group_value=None,
            horizon=horizon,
            row_count=int(str(metrics["row_count"])),
            **{
                key: metrics.get(key)
                for key in ("mae", "rmse", "wape", "smape", "mase", "bias", "mean_error", "median_absolute_error")
            },
            metrics_json=metrics,
        )
    )


def _artifact(
    db: Session,
    experiment: ForecastExperiment,
    run: ForecastModelRun,
    artifact_type: str,
    key: str,
    checksum: str,
    rows: int = 0,
) -> None:
    db.add(
        ForecastPredictionArtifact(
            experiment_id=experiment.id,
            model_run_id=run.id,
            artifact_type=artifact_type,
            storage_key=key,
            checksum=checksum,
            row_count=rows,
            metadata_json={},
        )
    )


def execute_experiment(
    db: Session, prepared_id: str, config: ForecastExperimentConfig, settings: Settings
) -> ForecastExperimentResponse:
    prepared, dataset, frame, splits, folds, safe_features = _validate(db, prepared_id, config, settings)
    models = list(config.enabled_models)
    if any(model in GBM_MODELS for model in models):
        models = list(
            dict.fromkeys(
                [
                    "naive_last",
                    "seasonal_naive",
                    "moving_average",
                    "drift",
                    "simple_exponential_smoothing",
                    "holt_linear",
                    "holt_winters",
                    "linear_regression",
                    "ridge_regression",
                    *models,
                ]
            )
        )
    if len(config.enabled_models) > settings.forecast_max_models_per_experiment:
        raise ForecastConfigurationError("Too many models requested")
    horizon = config.forecast_horizon or prepared.forecast_horizon or settings.forecast_default_horizon
    selection_metric = config.selection_metric or settings.forecast_default_selection_metric
    seasonal = config.seasonal_period or {
        "daily": settings.forecast_seasonal_period_daily,
        "weekly": settings.forecast_seasonal_period_weekly,
        "monthly": settings.forecast_seasonal_period_monthly,
        "hourly": 24,
    }.get(prepared.frequency, 4)
    windows = config.moving_average_windows or settings.forecast_moving_average_windows
    selected_folds = folds[-(config.backtest_folds or min(settings.forecast_backtest_folds, len(folds))) :]
    version = (
        db.scalar(
            select(func.max(ForecastExperiment.experiment_version)).where(
                ForecastExperiment.prepared_dataset_id == prepared_id
            )
        )
        or 0
    ) + 1
    config_data = config.model_dump()
    config_data.update(
        {
            "forecast_horizon": horizon,
            "selection_metric": selection_metric,
            "seasonal_period": seasonal,
            "moving_average_windows": windows,
            "backtest_folds": len(selected_folds),
        }
    )
    digest = hashlib.sha256(json.dumps(config_data, sort_keys=True, default=str).encode()).hexdigest()
    experiment = ForecastExperiment(
        prepared_dataset_id=prepared_id,
        experiment_version=version,
        forecasting_engine_version=settings.forecast_engine_version,
        status=ForecastExperimentStatus.training,
        target_column=config.target_column or prepared.target_column,
        date_column=prepared.date_column,
        group_columns_json=prepared.group_columns_json,
        frequency=prepared.frequency,
        forecast_horizon=horizon,
        selection_metric=selection_metric,
        random_seed=settings.forecast_random_seed,
        configuration_json=config_data,
        configuration_hash=digest,
        prepared_artifact_checksum=prepared.prepared_checksum or "",
        source_dataset_checksum=dataset.checksum_sha256,
        train_start=splits["train"]["start"],
        train_end=splits["train"]["end"],
        validation_start=splits["validation"]["start"],
        validation_end=splits["validation"]["end"],
        test_start=splits["test"]["start"],
        test_end=splits["test"]["end"],
        backtest_fold_count=len(selected_folds),
        metadata_json={
            "row_count": len(frame),
            "feature_count": prepared.feature_count,
            "group_count": int(frame[prepared.group_columns_json].drop_duplicates().shape[0])
            if prepared.group_columns_json
            else 1,
            "safe_linear_features": safe_features,
            "synthetic_data": "synthetic" in dataset.original_filename.lower()
            or "causalcast_marketing" in dataset.original_filename.lower(),
            "source_dataset_id": dataset.id,
        },
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    storage = ForecastStorageService(settings)
    train = _slice(frame, prepared.date_column, experiment.train_start, experiment.train_end)
    validation = _slice(frame, prepared.date_column, experiment.validation_start, experiment.validation_end)
    gbm_features, gbm_excluded = safe_gbm_features(
        prepared.features, experiment.target_column, prepared.group_columns_json
    )
    run_specs = [(name, window) for name in models for window in (windows if name == "moving_average" else [0])]
    try:
        for model_name, window in run_specs:
            definition = DEFINITIONS[model_name]
            display_name = f"moving_average_{window}" if model_name == "moving_average" else model_name
            run = ForecastModelRun(
                experiment_id=experiment.id,
                model_name=display_name,
                model_family=definition.family,
                model_version="1.0",
                status=ForecastModelStatus.fitting,
                hyperparameters_json={
                    "seasonal_period": seasonal,
                    **({"window": window} if window else {}),
                    "features": safe_features if model_name in {"linear_regression", "ridge_regression"} else [],
                },
                supports_groups=True,
                supports_trend=definition.supports_trend,
                supports_seasonality=definition.supports_seasonality,
                strategy=config.strategy,
                global_model=config.strategy == "global",
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            started = time.perf_counter()
            try:
                best_params: dict[str, object] = {}
                trial_records: list[dict[str, object]] = []
                if model_name in GBM_MODELS:
                    available, dependency_version = dependency_info(model_name)
                    if not available:
                        raise ValueError(f"Dependency unavailable for {model_name}")
                    run.dependency_version = dependency_version
                    run.tuning_method = "optuna_tpe_seeded"
                    tuning_folds = selected_folds[-(config.tuning_folds or min(2, len(selected_folds))) :]
                    best_params, trial_records, run.tuning_duration_ms = tune(
                        model_name,
                        frame,
                        tuning_folds,
                        prepared.date_column,
                        experiment.target_column,
                        gbm_features,
                        prepared.group_columns_json,
                        config.tuning_trials or settings.gbm_tuning_trials,
                        config.tuning_timeout_seconds or settings.gbm_tuning_timeout_seconds,
                        config.early_stopping_rounds or settings.gbm_early_stopping_rounds,
                        settings,
                        config.strategy,
                    )
                    run.tuning_trial_count = sum(x["status"] == "completed" for x in trial_records)
                    run.failed_trial_count = sum(x["status"] == "failed" for x in trial_records)
                    scores = [
                        float(str(x["backtest_metric"])) for x in trial_records if x["backtest_metric"] is not None
                    ]
                    run.best_score = min(scores)
                    run.feature_count = len(gbm_features)
                    run.hyperparameters_json = {
                        "best_parameters": best_params,
                        "features": gbm_features,
                        "excluded_features": gbm_excluded,
                    }
                    for record in trial_records:
                        db.add(
                            ForecastTuningTrial(
                                model_run_id=run.id,
                                trial_number=int(str(record["trial_number"])),
                                status=str(record["status"]),
                                parameters_json=record["parameters"] if isinstance(record["parameters"], dict) else {},
                                backtest_metric=record["backtest_metric"],
                                validation_metric=record["validation_metric"],
                                duration_ms=int(str(record["duration_ms"])),
                                failure_message=record["failure_message"],
                            )
                        )
                    validation_pred, fitted, run.best_iteration = fit_predict(
                        model_name,
                        train,
                        validation,
                        experiment.target_column,
                        gbm_features,
                        prepared.group_columns_json,
                        best_params,
                        settings,
                        config.early_stopping_rounds or settings.gbm_early_stopping_rounds,
                        config.strategy,
                    )
                    skipped: list[str] = []
                else:
                    validation_pred, fitted, skipped = forecast(
                        model_name,
                        train,
                        validation,
                        experiment.target_column,
                        prepared.group_columns_json,
                        prepared.date_column,
                        seasonal,
                        window,
                        safe_features,
                    )
                run.training_duration_ms = int((time.perf_counter() - started) * 1000)
                validation_file = _prediction_frame(
                    validation_pred, prepared.date_column, experiment.target_column, "validation", None
                )
                metrics = metric_set(
                    validation_file.actual.tolist(),
                    validation_file.prediction.tolist(),
                    train[experiment.target_column].dropna().tolist(),
                    seasonal,
                    settings.forecast_metric_epsilon,
                )
                run.validation_metrics_json = metrics
                run.residual_summary_json = residual_summary(
                    validation_file.actual.tolist(), validation_file.prediction.tolist()
                )
                if config.evaluate_per_group:
                    run.per_group_metrics_json = [
                        {
                            "group": str(group),
                            "metrics": metric_set(
                                group_frame.actual.tolist(),
                                group_frame.prediction.tolist(),
                                train[experiment.target_column].dropna().tolist(),
                                seasonal,
                                settings.forecast_metric_epsilon,
                            ),
                        }
                        for group, group_frame in validation_file.groupby("group", sort=True)
                    ]
                _add_evaluation(db, run, "validation", "validation", None, metrics, horizon)
                key, checksum = storage.write_frame(experiment.id, run.id, "validation_predictions", validation_file)
                _artifact(db, experiment, run, "validation_predictions", key, checksum, len(validation_file))
                run.status = ForecastModelStatus.backtesting
                fold_files: list[pd.DataFrame] = []
                fold_metrics: list[dict[str, object]] = []
                backtest_started = time.perf_counter()
                for fold in selected_folds:
                    fold_train = _slice(frame, prepared.date_column, fold["train_start"], fold["train_end"])
                    fold_validation = _slice(
                        frame, prepared.date_column, fold["validation_start"], fold["validation_end"]
                    )
                    if model_name in GBM_MODELS:
                        fold_pred, _, _ = fit_predict(
                            model_name,
                            fold_train,
                            fold_validation,
                            experiment.target_column,
                            gbm_features,
                            prepared.group_columns_json,
                            best_params,
                            settings,
                            config.early_stopping_rounds or settings.gbm_early_stopping_rounds,
                            config.strategy,
                        )
                        fold_skipped: list[str] = []
                    else:
                        fold_pred, _, fold_skipped = forecast(
                            model_name,
                            fold_train,
                            fold_validation,
                            experiment.target_column,
                            prepared.group_columns_json,
                            prepared.date_column,
                            seasonal,
                            window,
                            safe_features,
                        )
                    fold_file = _prediction_frame(
                        fold_pred, prepared.date_column, experiment.target_column, "backtest", int(fold["fold"])
                    )
                    fm = metric_set(
                        fold_file.actual.tolist(),
                        fold_file.prediction.tolist(),
                        fold_train[experiment.target_column].dropna().tolist(),
                        seasonal,
                        settings.forecast_metric_epsilon,
                    )
                    fm.update(
                        {
                            "fold": int(fold["fold"]),
                            "train_start": fold["train_start"],
                            "train_end": fold["train_end"],
                            "validation_start": fold["validation_start"],
                            "validation_end": fold["validation_end"],
                            "skipped_groups": fold_skipped,
                        }
                    )
                    fold_metrics.append(fm)
                    fold_files.append(fold_file)
                    _add_evaluation(db, run, "backtest_fold", "validation", int(fold["fold"]), fm, len(fold_validation))
                combined = pd.concat(fold_files)
                aggregate = metric_set(
                    combined.actual.tolist(),
                    combined.prediction.tolist(),
                    train[experiment.target_column].dropna().tolist(),
                    seasonal,
                    settings.forecast_metric_epsilon,
                )
                fold_wapes = [float(str(x["wape"])) for x in fold_metrics if x["wape"] is not None]
                aggregate["fold_wape_standard_deviation"] = float(np.std(fold_wapes))
                run.aggregate_backtest_metrics_json = aggregate
                run.per_fold_metrics_json = fold_metrics
                run.backtest_duration_ms = int((time.perf_counter() - backtest_started) * 1000)
                _add_evaluation(db, run, "backtest_aggregate", "validation", None, aggregate, len(combined))
                key, checksum = storage.write_frame(experiment.id, run.id, "backtest_predictions", combined)
                _artifact(db, experiment, run, "backtest_predictions", key, checksum, len(combined))
                model_key, model_checksum = storage.write_model(experiment.id, run.id, fitted)
                run.artifact_storage_key = model_key
                run.artifact_checksum = model_checksum
                _artifact(db, experiment, run, "model", model_key, model_checksum)
                if model_name in GBM_MODELS:
                    prep_key, prep_checksum = storage.write_joblib(
                        experiment.id, run.id, "preprocessing", fitted["preprocessing"]
                    )
                    _artifact(db, experiment, run, "preprocessing", prep_key, prep_checksum)
                    feature_importance, shap_summary = (
                        explanations(fitted, validation, settings.gbm_shap_sample_rows)
                        if config.generate_shap and settings.gbm_enable_shap
                        else ([], [])
                    )
                    for artifact_type, payload in (
                        ("feature_names", gbm_features),
                        ("hyperparameters", run.hyperparameters_json),
                        ("tuning_trials", trial_records),
                        ("feature_importance", feature_importance),
                        ("shap_summary", shap_summary),
                    ):
                        artifact_key, artifact_checksum = storage.write_json(
                            experiment.id, run.id, artifact_type, payload
                        )
                        _artifact(db, experiment, run, artifact_type, artifact_key, artifact_checksum)
                    run.explanation_available = bool(shap_summary)
                run.status = ForecastModelStatus.completed
                run.completed_at = datetime.now(UTC)
                run.hyperparameters_json["skipped_groups"] = skipped
            except Exception as exc:
                run.status = (
                    ForecastModelStatus.skipped
                    if isinstance(exc, ValueError) and "Insufficient" in str(exc)
                    else ForecastModelStatus.failed
                )
                run.failure_message = str(exc)[:500]
                run.completed_at = datetime.now(UTC)
            db.commit()
        experiment.status = ForecastExperimentStatus.selecting
        experiment.validation_completed_at = datetime.now(UTC)
        db.commit()
        valid = db.scalars(
            select(ForecastModelRun).where(
                ForecastModelRun.experiment_id == experiment.id,
                ForecastModelRun.status == ForecastModelStatus.completed,
            )
        ).all()
        valid = [
            x
            for x in valid
            if x.validation_metrics_json.get(selection_metric) is not None
            and x.aggregate_backtest_metrics_json.get(selection_metric) is not None
            and x.artifact_checksum
        ]
        if not valid:
            raise ForecastTrainingError("All requested baseline models failed or produced invalid metrics")
        ordered = sorted(
            valid,
            key=lambda x: (
                float(x.aggregate_backtest_metrics_json[selection_metric]),
                float(x.validation_metrics_json[selection_metric]),
                float(x.aggregate_backtest_metrics_json.get("fold_wape_standard_deviation", 0)),
                x.model_name,
            ),
        )
        for rank, run in enumerate(ordered, 1):
            run.rank = rank
            run.selection_score = rank + float(
                run.aggregate_backtest_metrics_json.get("fold_wape_standard_deviation", 0)
            )
        selected = ordered[0]
        selected.selected = True
        experiment.selected_model_run_id = selected.id
        experiment.status = ForecastExperimentStatus.test_evaluating
        db.commit()
        _evaluate_test(db, experiment, selected, frame, prepared, safe_features, seasonal, settings, storage)
        experiment.status = ForecastExperimentStatus.completed
        experiment.completed_at = datetime.now(UTC)
        db.commit()
        db.refresh(experiment)
        return _response(experiment)
    except Exception as exc:
        experiment.status = ForecastExperimentStatus.failed
        experiment.failure_message = str(exc)[:500]
        db.commit()
        raise


def _evaluate_test(
    db: Session,
    experiment: ForecastExperiment,
    run: ForecastModelRun,
    frame: pd.DataFrame,
    prepared: PreparedDataset,
    safe_features: list[str],
    seasonal: int,
    settings: Settings,
    storage: ForecastStorageService,
) -> None:
    if experiment.test_evaluated_at:
        raise FinalTestAlreadyEvaluatedError("Final test was already evaluated")
    pretest = _slice(frame, prepared.date_column, experiment.train_start, experiment.validation_end)
    test = _slice(frame, prepared.date_column, experiment.test_start, experiment.test_end)
    base_model = "moving_average" if run.model_name.startswith("moving_average_") else run.model_name
    window = int(run.model_name.rsplit("_", 1)[1]) if base_model == "moving_average" else 0
    if base_model in GBM_MODELS:
        features = [str(x) for x in run.hyperparameters_json.get("features", [])]
        parameters = dict(run.hyperparameters_json.get("best_parameters", {}))
        predicted, fitted, _ = fit_predict(
            base_model,
            pretest,
            test,
            experiment.target_column,
            features,
            prepared.group_columns_json,
            parameters,
            settings,
            0,
            run.strategy or "global",
        )
        skipped: list[str] = []
    else:
        predicted, fitted, skipped = forecast(
            base_model,
            pretest,
            test,
            experiment.target_column,
            prepared.group_columns_json,
            prepared.date_column,
            seasonal,
            window,
            safe_features,
        )
    output = _prediction_frame(predicted, prepared.date_column, experiment.target_column, "test", None)
    metrics = metric_set(
        output.actual.tolist(),
        output.prediction.tolist(),
        pretest[experiment.target_column].dropna().tolist(),
        seasonal,
        settings.forecast_metric_epsilon,
    )
    _add_evaluation(db, run, "final_test", "test", None, metrics, experiment.forecast_horizon)
    key, checksum = storage.write_frame(experiment.id, run.id, "test_predictions", output)
    _artifact(db, experiment, run, "test_predictions", key, checksum, len(output))
    key, checksum = storage.write_frame(experiment.id, run.id, "residuals", output[["date", "group", "residual"]])
    _artifact(db, experiment, run, "residuals", key, checksum, len(output))
    config_key, config_checksum = storage.write_json(
        experiment.id, run.id, "configuration", experiment.configuration_json
    )
    _artifact(db, experiment, run, "configuration", config_key, config_checksum)
    payload = {
        "validation": run.validation_metrics_json,
        "backtest": run.aggregate_backtest_metrics_json,
        "final_test": metrics,
    }
    metrics_key, metrics_checksum = storage.write_json(experiment.id, run.id, "metrics", payload)
    _artifact(db, experiment, run, "metrics", metrics_key, metrics_checksum)
    environment = (
        f"python={platform.python_version()}\n"
        f"pandas={pd.__version__}\n"
        f"numpy={np.__version__}\n"
        f"scikit-learn={sklearn.__version__}\n"
        f"statsmodels={statsmodels.__version__}\n"
        f"joblib={joblib.__version__}\n"
        f"random_seed={settings.forecast_random_seed}\n"
    )
    env_key, env_checksum = storage.write_text(experiment.id, run.id, "environment", environment, ".txt")
    _artifact(db, experiment, run, "environment", env_key, env_checksum)
    card = (
        "# CausalCast AI forecasting model card\n\n"
        f"Synthetic demonstration data: **{experiment.metadata_json.get('synthetic_data', False)}**\n\n"
        f"Model: `{run.model_name}`\n\n"
        f"Prepared dataset: `{experiment.prepared_dataset_id}` ({experiment.prepared_artifact_checksum})\n\n"
        "Selection used validation and expanding-window backtests only. "
        "Final test metrics were calculated once after selection.\n\n"
        "Feature importance and SHAP describe model contribution, not causal effect.\n\n"
        f"Test WAPE: {metrics.get('wape')}\n\n"
        f"Skipped groups: {skipped or 'none'}\n\n"
        "This trusted application-generated pickle/joblib artifact must never be loaded from an untrusted path.\n"
    )
    card_key, card_checksum = storage.write_text(experiment.id, run.id, "model_card", card, ".md")
    _artifact(db, experiment, run, "model_card", card_key, card_checksum)
    final_key, final_checksum = storage.write_model(experiment.id, run.id, fitted)
    run.artifact_storage_key = final_key
    run.artifact_checksum = final_checksum
    model_artifact = db.scalar(
        select(ForecastPredictionArtifact).where(
            ForecastPredictionArtifact.model_run_id == run.id,
            ForecastPredictionArtifact.artifact_type == "model",
        )
    )
    if model_artifact:
        model_artifact.storage_key = final_key
        model_artifact.checksum = final_checksum
    experiment.test_evaluated_at = datetime.now(UTC)
    db.commit()


def get_experiment(db: Session, experiment_id: str) -> ForecastExperimentResponse:
    item = db.get(ForecastExperiment, experiment_id)
    if not item:
        raise ForecastExperimentNotFoundError("Forecast experiment was not found")
    return _response(item)


def history(db: Session, prepared_id: str) -> ForecastExperimentHistoryResponse:
    items = db.scalars(
        select(ForecastExperiment)
        .where(ForecastExperiment.prepared_dataset_id == prepared_id)
        .order_by(ForecastExperiment.experiment_version.desc())
    ).all()
    return ForecastExperimentHistoryResponse(
        items=[
            ForecastExperimentSummary(
                id=x.id,
                prepared_dataset_id=x.prepared_dataset_id,
                experiment_version=x.experiment_version,
                status=x.status.value,
                target_column=x.target_column,
                frequency=x.frequency,
                selected_model_run_id=x.selected_model_run_id,
                created_at=x.created_at,
                completed_at=x.completed_at,
            )
            for x in items
        ]
    )


def model_runs(db: Session, experiment_id: str) -> list[ForecastModelRunSummary]:
    if not db.get(ForecastExperiment, experiment_id):
        raise ForecastExperimentNotFoundError("Forecast experiment was not found")
    return [
        _summary(x)
        for x in db.scalars(
            select(ForecastModelRun)
            .where(ForecastModelRun.experiment_id == experiment_id)
            .order_by(ForecastModelRun.rank.asc().nullslast(), ForecastModelRun.model_name)
        ).all()
    ]


def model_run(db: Session, run_id: str) -> ForecastModelRunResponse:
    item = db.get(ForecastModelRun, run_id)
    if not item:
        raise ForecastModelRunNotFoundError("Forecast model run was not found")
    return ForecastModelRunResponse(
        **_summary(item).model_dump(),
        model_version=item.model_version,
        hyperparameters=item.hyperparameters_json,
        fitted_on=item.fitted_on,
        supports_groups=item.supports_groups,
        supports_trend=item.supports_trend,
        supports_seasonality=item.supports_seasonality,
        artifact_checksum=item.artifact_checksum,
        per_fold_metrics=item.per_fold_metrics_json,
        per_group_metrics=item.per_group_metrics_json,
        residual_summary=ResidualSummary.model_validate(item.residual_summary_json)
        if item.residual_summary_json
        else None,
        completed_at=item.completed_at,
    )


def comparison(db: Session, experiment_id: str) -> ForecastComparisonResponse:
    experiment = db.get(ForecastExperiment, experiment_id)
    if not experiment:
        raise ForecastExperimentNotFoundError("Forecast experiment was not found")
    return ForecastComparisonResponse(
        experiment_id=experiment.id,
        selected_model_run_id=experiment.selected_model_run_id,
        selection_method=(
            "Ascending backtest metric, then validation metric, fold stability, "
            "and stable model identifier; test metrics excluded."
        ),
        items=model_runs(db, experiment_id),
    )


def predictions(
    db: Session,
    experiment_id: str,
    run_id: str | None,
    split: str,
    fold: int | None,
    group: str | None,
    page: int,
    page_size: int,
    settings: Settings,
) -> ForecastPredictionListResponse:
    experiment = db.get(ForecastExperiment, experiment_id)
    if not experiment:
        raise ForecastExperimentNotFoundError("Forecast experiment was not found")
    selected_run = run_id or experiment.selected_model_run_id
    if not selected_run:
        raise ForecastModelRunNotFoundError("No model run is available")
    artifact_type = {
        "validation": "validation_predictions",
        "backtest": "backtest_predictions",
        "test": "test_predictions",
    }.get(split)
    artifact = db.scalar(
        select(ForecastPredictionArtifact).where(
            ForecastPredictionArtifact.experiment_id == experiment_id,
            ForecastPredictionArtifact.model_run_id == selected_run,
            ForecastPredictionArtifact.artifact_type == artifact_type,
        )
    )
    if not artifact:
        raise ForecastArtifactMissingError("Prediction artifact is unavailable")
    path = ForecastStorageService(settings).resolve(artifact.storage_key)
    if _hash(path) != artifact.checksum:
        raise ForecastChecksumMismatchError("Forecast artifact checksum mismatch")
    frame = pd.read_csv(path)
    frame = frame[frame["fold"].eq(fold)] if fold is not None else frame
    frame = frame[frame["group"].astype(str).eq(group)] if group is not None else frame
    total = len(frame)
    subset = frame.iloc[(page - 1) * page_size : page * page_size]
    items = [
        ForecastPredictionRow(
            date=str(row.date),
            actual=float(row.actual),
            prediction=float(row.prediction),
            residual=float(row.residual),
            split=str(row.split),
            fold=int(row.fold) if not pd.isna(row.fold) else None,
            group=str(row.group) if not pd.isna(row.group) else None,
        )
        for row in subset.itertuples()
    ]
    return ForecastPredictionListResponse(
        experiment_id=experiment_id,
        model_run_id=selected_run,
        split=split,
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=math.ceil(total / page_size) if total else 0,
    )


def stats(db: Session) -> ForecastStatsResponse:
    experiments = db.scalars(select(ForecastExperiment).order_by(ForecastExperiment.created_at.desc())).all()
    completed = [x for x in experiments if x.status == ForecastExperimentStatus.completed]
    selected_ids = [x.selected_model_run_id for x in completed if x.selected_model_run_id]
    selected_runs = (
        db.scalars(select(ForecastModelRun).where(ForecastModelRun.id.in_(selected_ids))).all() if selected_ids else []
    )
    distribution: dict[str, int] = {}
    for run in selected_runs:
        distribution[run.model_name] = distribution.get(run.model_name, 0) + 1
    test_wapes = [
        float(e.metrics_json["wape"])
        for e in db.scalars(select(ForecastEvaluation).where(ForecastEvaluation.evaluation_type == "final_test")).all()
        if e.metrics_json.get("wape") is not None
    ]
    ready = (
        db.scalar(
            select(func.count())
            .select_from(PreparedDataset)
            .where(
                PreparedDataset.status == PreparationStatus.completed,
                PreparedDataset.readiness_status == PreparationReadiness.model_ready,
            )
        )
        or 0
    )
    forecasted = len({x.prepared_dataset_id for x in completed})
    return ForecastStatsResponse(
        total_experiments=len(experiments),
        completed_experiments=len(completed),
        failed_experiments=sum(x.status == ForecastExperimentStatus.failed for x in experiments),
        selected_model_distribution=distribution,
        average_test_wape=float(np.mean(test_wapes)) if test_wapes else None,
        datasets_awaiting_forecasting=max(ready - forecasted, 0),
        latest_experiment_status=experiments[0].status.value if experiments else None,
    )


def tuning_summary(db: Session, run_id: str) -> TuningSummaryResponse:
    run = db.scalar(
        select(ForecastModelRun)
        .options(selectinload(ForecastModelRun.tuning_trials))
        .where(ForecastModelRun.id == run_id)
    )
    if not run:
        raise ForecastModelRunNotFoundError("Forecast model run was not found")
    return TuningSummaryResponse(
        model_run_id=run.id,
        method=run.tuning_method,
        completed_trials=run.tuning_trial_count,
        failed_trials=run.failed_trial_count,
        best_score=run.best_score,
        best_parameters=dict(run.hyperparameters_json.get("best_parameters", {})),
        duration_ms=run.tuning_duration_ms,
        items=[
            TuningTrialSummary(
                trial_number=x.trial_number,
                status=x.status,
                parameters=x.parameters_json,
                backtest_metric=x.backtest_metric,
                validation_metric=x.validation_metric,
                duration_ms=x.duration_ms,
                failure_message=x.failure_message,
            )
            for x in sorted(run.tuning_trials, key=lambda value: value.trial_number)[:100]
        ],
    )


def _json_artifact(db: Session, run_id: str, artifact_type: str, settings: Settings) -> object:
    artifact = db.scalar(
        select(ForecastPredictionArtifact).where(
            ForecastPredictionArtifact.model_run_id == run_id,
            ForecastPredictionArtifact.artifact_type == artifact_type,
        )
    )
    if not artifact:
        raise ForecastArtifactMissingError(f"{artifact_type.replace('_', ' ').title()} artifact is unavailable")
    path = ForecastStorageService(settings).resolve(artifact.storage_key)
    if _hash(path) != artifact.checksum:
        raise ForecastChecksumMismatchError("Forecast artifact checksum mismatch")
    return json.loads(path.read_text(encoding="utf-8"))


def feature_importance(db: Session, run_id: str, settings: Settings) -> FeatureImportanceResponse:
    payload = _json_artifact(db, run_id, "feature_importance", settings)
    return FeatureImportanceResponse(model_run_id=run_id, items=payload)


def shap_summary(db: Session, run_id: str, settings: Settings, limit: int) -> ShapExplanationResponse:
    payload = _json_artifact(db, run_id, "shap_summary", settings)
    items = payload if isinstance(payload, list) else []
    return ShapExplanationResponse(
        model_run_id=run_id, sample_rows=min(settings.gbm_shap_sample_rows, limit), items=items[:limit]
    )


def gbm_stats(db: Session) -> GradientBoostingStatsResponse:
    runs = db.scalars(select(ForecastModelRun).where(ForecastModelRun.model_family == "gradient_boosting")).all()
    wins: dict[str, int] = {}
    selected = [run for run in runs if run.selected]
    for run in selected:
        wins[run.model_name] = wins.get(run.model_name, 0) + 1
    improvements: list[float] = []
    for run in selected:
        peers = db.scalars(
            select(ForecastModelRun).where(
                ForecastModelRun.experiment_id == run.experiment_id,
                ForecastModelRun.model_family != "gradient_boosting",
                ForecastModelRun.status == ForecastModelStatus.completed,
            )
        ).all()
        baseline = [
            float(x.aggregate_backtest_metrics_json["wape"])
            for x in peers
            if x.aggregate_backtest_metrics_json.get("wape") is not None
        ]
        if baseline and run.aggregate_backtest_metrics_json.get("wape") is not None:
            improvements.append((min(baseline) - float(run.aggregate_backtest_metrics_json["wape"])) / min(baseline))
    durations = [run.tuning_duration_ms for run in runs if run.tuning_duration_ms]
    return GradientBoostingStatsResponse(
        completed_experiments=len({run.experiment_id for run in runs if run.status == ForecastModelStatus.completed}),
        model_wins=wins,
        average_tuning_duration_ms=float(np.mean(durations)) if durations else None,
        average_improvement_over_baseline=float(np.mean(improvements)) if improvements else None,
        failed_model_count=sum(run.status == ForecastModelStatus.failed for run in runs),
    )
