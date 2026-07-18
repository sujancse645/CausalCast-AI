from collections.abc import Callable
from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.deep_forecasting import (
    DeepForecastCapabilityResponse,
    DeepForecastDependencyResponse,
    DeepForecastHardwareResponse,
    DeepForecastModelDefinitionResponse,
    DeepForecastReadinessRequest,
    DeepForecastReadinessResponse,
)
from app.services.deep_forecasting.capability_service import capabilities
from app.services.deep_forecasting.data_pipeline import analyze_readiness, latest_readiness
from app.services.deep_forecasting.dependency_service import dependency_report
from app.services.deep_forecasting.errors import (
    DeepArtifactStorageError,
    DeepConfigurationError,
    DeepDatasetNotReadyError,
    DeepHardwareConfigurationError,
)
from app.services.deep_forecasting.hardware_service import hardware_report
from app.services.deep_forecasting.model_registry import deep_models

router = APIRouter(tags=["deep-forecasting"])
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]
T = TypeVar("T")


def _safe(call: Callable[[], T]) -> T:
    try:
        return call()
    except DeepDatasetNotReadyError as exc:
        code = status.HTTP_404_NOT_FOUND if "not found" in str(exc) or "not been analyzed" in str(exc) else 409
        raise HTTPException(code, detail=str(exc)) from exc
    except (DeepConfigurationError, DeepHardwareConfigurationError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except DeepArtifactStorageError as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Deep artifact persistence failed safely"
        ) from exc


@router.get("/forecasting/deep/capabilities", response_model=DeepForecastCapabilityResponse)
def deep_capabilities(settings: Config) -> DeepForecastCapabilityResponse:
    return _safe(lambda: capabilities(settings))


@router.get("/forecasting/deep/models", response_model=list[DeepForecastModelDefinitionResponse])
def deep_model_registry(settings: Config) -> list[DeepForecastModelDefinitionResponse]:
    return deep_models(settings)


@router.get("/forecasting/deep/hardware", response_model=DeepForecastHardwareResponse)
def deep_hardware(settings: Config) -> DeepForecastHardwareResponse:
    return _safe(lambda: hardware_report(settings))


@router.get("/forecasting/deep/dependencies", response_model=list[DeepForecastDependencyResponse])
def deep_dependencies() -> list[DeepForecastDependencyResponse]:
    return list(dependency_report())


@router.post(
    "/preparations/{prepared_id}/deep-readiness",
    response_model=DeepForecastReadinessResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deep_readiness(
    prepared_id: UUID, request: DeepForecastReadinessRequest, db: Db, settings: Config
) -> DeepForecastReadinessResponse:
    return _safe(lambda: analyze_readiness(db, str(prepared_id), request, settings))


@router.get("/preparations/{prepared_id}/deep-readiness", response_model=DeepForecastReadinessResponse)
def get_deep_readiness(prepared_id: UUID, db: Db) -> DeepForecastReadinessResponse:
    return _safe(lambda: latest_readiness(db, str(prepared_id)))
