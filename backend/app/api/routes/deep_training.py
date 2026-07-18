from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.deep_learning.services.training import DeepTrainingService
from app.schemas.deep_forecasting import (
    DeepCheckpointResumeRequest,
    DeepCheckpointResumeResponse,
    DeepTrainingExperimentResponse,
    DeepTrainingListResponse,
    NHiTSTrainingRequest,
)

router = APIRouter(prefix="/deep", tags=["deep-training"])
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


def service(db: Db, settings: Config) -> DeepTrainingService:
    return DeepTrainingService(db, settings)


Training = Annotated[DeepTrainingService, Depends(service)]


def _translate(exc: Exception) -> HTTPException:
    if isinstance(exc, FileNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    return HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Deep training failed safely")


@router.post("/train/nhits", response_model=DeepTrainingExperimentResponse, status_code=status.HTTP_201_CREATED)
def train_nhits(request: NHiTSTrainingRequest, training: Training) -> DeepTrainingExperimentResponse:
    try:
        return training.train_nhits(request)
    except Exception as exc:
        raise _translate(exc) from exc


@router.get("/train/status", response_model=DeepTrainingListResponse)
def training_status(training: Training, limit: int = Query(default=20, ge=1, le=100)) -> DeepTrainingListResponse:
    return training.list_experiments(limit)


@router.get("/experiments", response_model=DeepTrainingListResponse)
def deep_experiments(training: Training, limit: int = Query(default=100, ge=1, le=100)) -> DeepTrainingListResponse:
    return training.list_experiments(limit)


@router.get("/experiments/{identifier}", response_model=DeepTrainingExperimentResponse)
def deep_experiment(identifier: str, training: Training) -> DeepTrainingExperimentResponse:
    try:
        return training.get(identifier)
    except Exception as exc:
        raise _translate(exc) from exc


@router.post("/checkpoint/resume", response_model=DeepCheckpointResumeResponse, status_code=status.HTTP_201_CREATED)
def resume_checkpoint(request: DeepCheckpointResumeRequest, training: Training) -> DeepCheckpointResumeResponse:
    try:
        return training.resume(request)
    except Exception as exc:
        raise _translate(exc) from exc
