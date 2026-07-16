from collections.abc import Callable
from pathlib import Path
from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.models.forecasting import ForecastPredictionArtifact
from app.schemas.forecasting import (
    FeatureImportanceResponse,
    ForecastComparisonResponse,
    ForecastExperimentCreateRequest,
    ForecastExperimentHistoryResponse,
    ForecastExperimentResponse,
    ForecastModelDefinition,
    ForecastModelRunResponse,
    ForecastModelRunSummary,
    ForecastPredictionListResponse,
    ForecastStatsResponse,
    GradientBoostingStatsResponse,
    ShapExplanationResponse,
    TuningSummaryResponse,
)
from app.services.forecast_storage_service import ForecastStorageService
from app.services.forecasting_service import (
    ForecastArtifactMissingError,
    ForecastChecksumMismatchError,
    ForecastConfigurationError,
    ForecastExperimentNotFoundError,
    ForecastModelRunNotFoundError,
    InsufficientForecastHistoryError,
    PreparedDatasetNotReadyForForecastingError,
    comparison,
    execute_experiment,
    feature_importance,
    gbm_stats,
    get_experiment,
    history,
    model_registry,
    model_run,
    model_runs,
    predictions,
    shap_summary,
    stats,
    tuning_summary,
)

router = APIRouter(tags=["forecasting"])
T = TypeVar("T")
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


def _safe(call: Callable[[], T]) -> T:
    try:
        return call()
    except (ForecastExperimentNotFoundError, ForecastModelRunNotFoundError, ForecastArtifactMissingError) as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ForecastChecksumMismatchError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except (PreparedDatasetNotReadyForForecastingError, InsufficientForecastHistoryError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except ForecastConfigurationError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@router.post(
    "/preparations/{prepared_id}/forecast-experiments", response_model=ForecastExperimentResponse, status_code=201
)
def create(
    prepared_id: UUID, request: ForecastExperimentCreateRequest, db: Db, settings: Config
) -> ForecastExperimentResponse:
    return _safe(lambda: execute_experiment(db, str(prepared_id), request.config, settings))


@router.get("/preparations/{prepared_id}/forecast-experiments", response_model=ForecastExperimentHistoryResponse)
def experiment_history(prepared_id: UUID, db: Db) -> ForecastExperimentHistoryResponse:
    return history(db, str(prepared_id))


@router.get("/forecast-experiments/{experiment_id}", response_model=ForecastExperimentResponse)
def detail(experiment_id: UUID, db: Db) -> ForecastExperimentResponse:
    return _safe(lambda: get_experiment(db, str(experiment_id)))


@router.get("/forecast-experiments/{experiment_id}/models", response_model=list[ForecastModelRunSummary])
def runs(experiment_id: UUID, db: Db) -> list[ForecastModelRunSummary]:
    return _safe(lambda: model_runs(db, str(experiment_id)))


@router.get("/forecast-experiments/{experiment_id}/metrics", response_model=list[ForecastModelRunSummary])
def metrics(experiment_id: UUID, db: Db) -> list[ForecastModelRunSummary]:
    return _safe(lambda: model_runs(db, str(experiment_id)))


@router.get("/forecast-experiments/{experiment_id}/comparison", response_model=ForecastComparisonResponse)
def compare(experiment_id: UUID, db: Db) -> ForecastComparisonResponse:
    return _safe(lambda: comparison(db, str(experiment_id)))


@router.get("/forecast-experiments/{experiment_id}/predictions", response_model=ForecastPredictionListResponse)
def prediction_list(
    experiment_id: UUID,
    db: Db,
    settings: Config,
    model_run_id: UUID | None = None,
    split: Annotated[str, Query(pattern="^(validation|backtest|test)$")] = "test",
    fold: int | None = None,
    group: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 100,
) -> ForecastPredictionListResponse:
    return _safe(
        lambda: predictions(
            db,
            str(experiment_id),
            str(model_run_id) if model_run_id else None,
            split,
            fold,
            group,
            page,
            page_size,
            settings,
        )
    )


@router.get("/forecast-model-runs/{run_id}", response_model=ForecastModelRunResponse)
def run_detail(run_id: UUID, db: Db) -> ForecastModelRunResponse:
    return _safe(lambda: model_run(db, str(run_id)))


@router.get("/forecast-model-runs/{run_id}/download", response_class=FileResponse)
def download(
    run_id: UUID,
    db: Db,
    settings: Config,
    artifact_type: Annotated[
        str,
        Query(
            pattern="^(model|preprocessing|feature_names|hyperparameters|tuning_trials|feature_importance|shap_summary|configuration|metrics|model_card|environment|validation_predictions|backtest_predictions|test_predictions|residuals)$"
        ),
    ],
) -> FileResponse:
    artifact = db.scalar(
        select(ForecastPredictionArtifact).where(
            ForecastPredictionArtifact.model_run_id == str(run_id),
            ForecastPredictionArtifact.artifact_type == artifact_type,
        )
    )
    if not artifact:
        raise HTTPException(404, detail="Forecast artifact is unavailable")
    storage = ForecastStorageService(settings)
    path = storage.resolve(artifact.storage_key)
    if storage.checksum(path) != artifact.checksum:
        raise HTTPException(409, detail="Forecast artifact checksum mismatch")
    media = (
        "text/csv"
        if path.suffix == ".csv"
        else "application/json"
        if path.suffix == ".json"
        else "text/markdown"
        if path.suffix == ".md"
        else "application/octet-stream"
    )
    return FileResponse(path, media_type=media, filename=f"causalcast-{artifact_type}{Path(path).suffix}")


@router.get("/forecasting/models", response_model=list[ForecastModelDefinition])
def registry(settings: Config) -> list[ForecastModelDefinition]:
    return model_registry(settings)


@router.get("/forecasting/stats", response_model=ForecastStatsResponse)
def forecast_stats(db: Db) -> ForecastStatsResponse:
    return stats(db)


@router.get("/forecast-model-runs/{run_id}/tuning", response_model=TuningSummaryResponse)
def run_tuning(run_id: UUID, db: Db) -> TuningSummaryResponse:
    return _safe(lambda: tuning_summary(db, str(run_id)))


@router.get("/forecast-model-runs/{run_id}/feature-importance", response_model=FeatureImportanceResponse)
def run_importance(run_id: UUID, db: Db, settings: Config) -> FeatureImportanceResponse:
    return _safe(lambda: feature_importance(db, str(run_id), settings))


@router.get("/forecast-model-runs/{run_id}/shap", response_model=ShapExplanationResponse)
def run_shap(
    run_id: UUID, db: Db, settings: Config, limit: Annotated[int, Query(ge=1, le=500)] = 50
) -> ShapExplanationResponse:
    return _safe(lambda: shap_summary(db, str(run_id), settings, limit))


@router.get("/forecasting/gradient-boosting/stats", response_model=GradientBoostingStatsResponse)
def gradient_stats(db: Db) -> GradientBoostingStatsResponse:
    return gbm_stats(db)
