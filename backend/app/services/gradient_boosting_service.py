import time
from typing import Any

import numpy as np
import optuna
import pandas as pd
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor, early_stopping, log_evaluation
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBRegressor

from app.core.config import Settings
from app.services.forecast_metrics import metric_set

GBM_MODELS = {"lightgbm_regressor", "xgboost_regressor", "catboost_regressor"}


class GradientBoostingDependencyUnavailableError(RuntimeError):
    pass


class GradientBoostingConfigurationError(ValueError):
    pass


class GradientBoostingTrainingError(RuntimeError):
    pass


class HyperparameterTuningError(RuntimeError):
    pass


class NoSafeFeaturesError(ValueError):
    pass


class FeatureCatalogMismatchError(ValueError):
    pass


class ShapExplanationError(RuntimeError):
    pass


class ModelArtifactLoadError(RuntimeError):
    pass


def safe_gbm_features(features: list[Any], target: str, groups: list[str]) -> tuple[list[str], list[str]]:
    allowed: list[str] = []
    excluded: list[str] = []
    for feature in features:
        name = str(feature.feature_name)
        safe = (
            feature.included
            and name != target
            and feature.leakage_risk == "none"
            and feature.availability_type in {"known_in_advance", "observed_at_prediction_time"}
            and feature.feature_type not in {"target", "date", "identifier", "text"}
        )
        # Precomputed target lags inside a multi-step holdout would expose realized holdout targets.
        if feature.feature_type in {"lag", "rolling"}:
            safe = False
        (allowed if safe else excluded).append(name)
    allowed.extend(group for group in groups if group not in allowed)
    if not allowed:
        raise NoSafeFeaturesError("No leakage-safe gradient-boosting features remain")
    return list(dict.fromkeys(allowed)), list(dict.fromkeys(excluded))


def _preprocessor(train: pd.DataFrame, features: list[str]) -> tuple[ColumnTransformer, list[str]]:
    missing = [name for name in features if name not in train]
    if missing:
        raise FeatureCatalogMismatchError("Feature catalog columns are missing from the artifact")
    numeric = [name for name in features if pd.api.types.is_numeric_dtype(train[name])]
    categorical = [name for name in features if name not in numeric]
    transforms: list[tuple[str, Any, list[str]]] = []
    if numeric:
        transforms.append(("numeric", SimpleImputer(strategy="median", add_indicator=True), numeric))
    if categorical:
        transforms.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="most_frequent")),
                        ("encode", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
                    ]
                ),
                categorical,
            )
        )
    return ColumnTransformer(transforms, verbose_feature_names_out=False), categorical


def _estimator(model: str, params: dict[str, object], settings: Settings) -> Any:
    common = {"random_state": settings.gbm_random_seed}
    if model == "lightgbm_regressor":
        estimator_class: Any = LGBMRegressor
        return estimator_class(**common, n_jobs=settings.gbm_n_jobs, verbosity=-1, **params)
    if model == "xgboost_regressor":
        return XGBRegressor(**common, n_jobs=settings.gbm_n_jobs, objective="reg:squarederror", **params)
    if model == "catboost_regressor":
        translated = dict(params)
        translated["depth"] = translated.pop("max_depth")
        translated["rsm"] = translated.pop("colsample_bytree")
        translated["l2_leaf_reg"] = translated.pop("reg_lambda")
        translated.pop("reg_alpha")
        translated["bootstrap_type"] = "Bernoulli"
        return CatBoostRegressor(
            **common,
            thread_count=settings.gbm_n_jobs,
            loss_function="RMSE",
            verbose=False,
            allow_writing_files=False,
            **translated,
        )
    raise GradientBoostingConfigurationError(f"Unsupported gradient-boosting model: {model}")


def fit_predict(
    model: str,
    train: pd.DataFrame,
    future: pd.DataFrame,
    target: str,
    features: list[str],
    groups: list[str],
    params: dict[str, object],
    settings: Settings,
    early_stopping_rounds: int,
    strategy: str = "global",
) -> tuple[pd.DataFrame, dict[str, Any], int | None]:
    if strategy == "per_group" and groups:
        outputs: list[pd.DataFrame] = []
        artifacts: dict[str, object] = {}
        iterations: list[int] = []
        for key, group_future in future.groupby(groups, sort=True):
            values = key if isinstance(key, tuple) else (key,)
            mask = pd.Series(True, index=train.index)
            for column, value in zip(groups, values, strict=True):
                mask &= train[column].eq(value)
            group_train = train.loc[mask]
            if len(group_train) < 10:
                raise GradientBoostingTrainingError(f"Insufficient group history for {values}")
            predicted, artifact, iteration = fit_predict(
                model,
                group_train,
                group_future,
                target,
                features,
                groups,
                params,
                settings,
                early_stopping_rounds,
                "global",
            )
            label = " | ".join(map(str, values))
            outputs.append(predicted)
            artifacts[label] = artifact
            if iteration is not None:
                iterations.append(iteration)
        combined_artifact = {"strategy": "per_group", "models": artifacts, "features": features}
        return pd.concat(outputs).sort_index(), combined_artifact, max(iterations) if iterations else None
    train_mask = train[target].notna()
    processor, categorical = _preprocessor(train.loc[train_mask], features)
    x_train = processor.fit_transform(train.loc[train_mask, features])
    x_future = processor.transform(future[features])
    y_train = train.loc[train_mask, target].to_numpy(dtype=float)
    future_mask = future[target].notna()
    estimator = _estimator(model, params, settings)
    eval_set = [(x_future[future_mask], future.loc[future_mask, target].to_numpy(dtype=float))]
    if early_stopping_rounds <= 0:
        estimator.fit(x_train, y_train)
    elif model == "lightgbm_regressor":
        estimator.fit(
            x_train,
            y_train,
            eval_set=eval_set,
            callbacks=[early_stopping(early_stopping_rounds, verbose=False), log_evaluation(0)],
        )
    else:
        estimator.set_params(early_stopping_rounds=early_stopping_rounds)
        estimator.fit(x_train, y_train, eval_set=eval_set, verbose=False)
    result = future.copy()
    result["prediction"] = estimator.predict(x_future)
    result["group"] = result[groups].astype(str).agg(" | ".join, axis=1) if groups else "all"
    best_iteration = getattr(estimator, "best_iteration_", getattr(estimator, "best_iteration", None))
    artifact = {"preprocessing": processor, "model": estimator, "features": features, "categorical": categorical}
    return result, artifact, int(best_iteration) if best_iteration is not None else None


def _parameters(trial: optuna.Trial, settings: Settings) -> dict[str, object]:
    return {
        "n_estimators": trial.suggest_int(
            "n_estimators", settings.gbm_estimators_min, settings.gbm_estimators_max, step=50
        ),
        "max_depth": trial.suggest_int("max_depth", settings.gbm_max_depth_min, settings.gbm_max_depth_max),
        "learning_rate": trial.suggest_float(
            "learning_rate", settings.gbm_learning_rate_min, settings.gbm_learning_rate_max, log=True
        ),
        "subsample": trial.suggest_float("subsample", settings.gbm_subsample_min, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", settings.gbm_colsample_min, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 0.0, settings.gbm_reg_alpha_max),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.0, settings.gbm_reg_lambda_max),
    }


def tune(
    model: str,
    frame: pd.DataFrame,
    folds: list[dict[str, Any]],
    date: str,
    target: str,
    features: list[str],
    groups: list[str],
    trials: int,
    timeout: int,
    early_rounds: int,
    settings: Settings,
    strategy: str = "global",
) -> tuple[dict[str, object], list[dict[str, object]], int]:
    records: list[dict[str, object]] = []
    started = time.perf_counter()

    def objective(trial: optuna.Trial) -> float:
        trial_started = time.perf_counter()
        params = _parameters(trial, settings)
        try:
            values: list[float] = []
            for fold in folds:
                train = frame[(frame[date] >= fold["train_start"]) & (frame[date] <= fold["train_end"])]
                valid = frame[(frame[date] >= fold["validation_start"]) & (frame[date] <= fold["validation_end"])]
                predicted, _, _ = fit_predict(
                    model, train, valid, target, features, groups, params, settings, early_rounds, strategy
                )
                metrics = metric_set(
                    valid[target].tolist(),
                    predicted.prediction.tolist(),
                    train[target].dropna().tolist(),
                    1,
                    settings.forecast_metric_epsilon,
                )
                value = metrics[settings.gbm_primary_metric]
                if value is None:
                    raise GradientBoostingTrainingError("Tuning metric is undefined")
                values.append(float(str(value)))
            score = float(np.mean(values))
            records.append(
                {
                    "trial_number": trial.number,
                    "status": "completed",
                    "parameters": params,
                    "backtest_metric": score,
                    "validation_metric": score,
                    "duration_ms": int((time.perf_counter() - trial_started) * 1000),
                    "failure_message": None,
                }
            )
            return score
        except Exception as exc:
            records.append(
                {
                    "trial_number": trial.number,
                    "status": "failed",
                    "parameters": params,
                    "backtest_metric": None,
                    "validation_metric": None,
                    "duration_ms": int((time.perf_counter() - trial_started) * 1000),
                    "failure_message": str(exc)[:500],
                }
            )
            raise

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=settings.gbm_random_seed))
    study.optimize(objective, n_trials=trials, timeout=timeout, catch=(Exception,), n_jobs=1, show_progress_bar=False)
    if not study.best_trials:
        raise HyperparameterTuningError("All hyperparameter trials failed")
    return dict(study.best_params), records, int((time.perf_counter() - started) * 1000)


def explanations(
    artifact: dict[str, Any], sample: pd.DataFrame, limit: int
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    import shap

    processor = artifact["preprocessing"]
    estimator = artifact["model"]
    features = artifact["features"]
    bounded = sample[features].head(limit)
    transformed = processor.transform(bounded)
    names = [str(x) for x in processor.get_feature_names_out()]
    native = np.asarray(estimator.feature_importances_, dtype=float)
    native = native / native.sum() if native.sum() else native
    values = np.asarray(shap.TreeExplainer(estimator).shap_values(transformed), dtype=float)
    mean_abs = np.mean(np.abs(values), axis=0)
    mean = np.mean(values, axis=0)
    importance: list[dict[str, object]] = [
        {
            "feature": name,
            "native_importance": float(native[i]),
            "shap_importance": float(mean_abs[i]),
            "feature_type": "transformed",
            "leakage_status": "none",
        }
        for i, name in enumerate(names)
    ]
    summary: list[dict[str, object]] = [
        {
            "feature": name,
            "mean_absolute_shap": float(mean_abs[i]),
            "mean_shap": float(mean[i]),
            "direction": "positive" if mean[i] > 0 else "negative" if mean[i] < 0 else "neutral",
        }
        for i, name in enumerate(names)
    ]
    return sorted(importance, key=lambda x: float(str(x["shap_importance"])), reverse=True), sorted(
        summary, key=lambda x: float(str(x["mean_absolute_shap"])), reverse=True
    )
