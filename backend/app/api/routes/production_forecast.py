from collections.abc import Callable
from typing import Annotated, TypeVar

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.production_forecast import (
    ProductionDatasetMetadata,
    ProductionDatasetSummary,
    ProductionForecastRequest,
    ProductionForecastResponse,
    ProductionModelSummary,
    ProductionReportResponse,
)
from app.services.production_forecast_service import (
    ProductionAssetInvalidError,
    ProductionAssetNotFoundError,
    ProductionForecastService,
    get_production_forecast_service,
)

router = APIRouter(tags=["production-forecasting"])
ForecastService = Annotated[ProductionForecastService, Depends(get_production_forecast_service)]
ResponseT = TypeVar("ResponseT")


def _safe(call: Callable[[], ResponseT]) -> ResponseT:
    try:
        return call()
    except ProductionAssetNotFoundError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ProductionAssetInvalidError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@router.get("/production-models", response_model=list[ProductionModelSummary])
def models(forecasts: ForecastService) -> list[ProductionModelSummary]:
    return forecasts.models()


@router.get("/forecast-datasets", response_model=list[ProductionDatasetSummary])
def datasets(forecasts: ForecastService) -> list[ProductionDatasetSummary]:
    return forecasts.datasets()


@router.get("/forecast-datasets/{dataset}/metadata", response_model=ProductionDatasetMetadata)
def metadata(dataset: str, forecasts: ForecastService) -> ProductionDatasetMetadata:
    return _safe(lambda: forecasts.metadata(dataset))


@router.post("/forecast", response_model=ProductionForecastResponse)
def forecast(request: ProductionForecastRequest, forecasts: ForecastService) -> ProductionForecastResponse:
    return _safe(lambda: forecasts.forecast(request.dataset, request.horizon, request.series))


@router.get("/reports/{dataset}", response_model=ProductionReportResponse)
def report(dataset: str, forecasts: ForecastService) -> ProductionReportResponse:
    return _safe(lambda: forecasts.report(dataset))
