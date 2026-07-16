from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import (
    DatasetNotReadyForQualityAnalysisError,
    MissingConfirmedSchemaError,
    QualityReportNotFoundError,
)
from app.schemas.quality import (
    QualityAnalysisRequest,
    QualityFindingListResponse,
    QualityHistoryResponse,
    QualityReportDetail,
    QualityRuleDefinition,
    QualityRuleListResponse,
    QualityStatsResponse,
)
from app.services.data_quality_service import (
    analyze_quality,
    quality_detail,
    quality_findings,
    quality_history,
    quality_stats,
)
from app.services.quality_rule_registry import RULES

router = APIRouter(tags=["data quality"])
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


@router.get("/quality/rules", response_model=QualityRuleListResponse)
def rules() -> QualityRuleListResponse:
    return QualityRuleListResponse(
        items=[
            QualityRuleDefinition(code=r.code, category=r.category, title=r.title, description=r.description)
            for r in RULES
        ]
    )


@router.get("/datasets/quality/stats", response_model=QualityStatsResponse)
def stats(db: Db) -> QualityStatsResponse:
    return quality_stats(db)


@router.post(
    "/datasets/{dataset_id}/quality/analyze", response_model=QualityReportDetail, status_code=status.HTTP_201_CREATED
)
def analyze(
    dataset_id: str, request: QualityAnalysisRequest, db: Db, settings: Config
) -> QualityReportDetail | JSONResponse:
    try:
        return analyze_quality(db, dataset_id, settings, request.notes)
    except DatasetNotReadyForQualityAnalysisError as exc:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    except MissingConfirmedSchemaError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


@router.get("/datasets/{dataset_id}/quality", response_model=QualityReportDetail)
def active(dataset_id: str, db: Db) -> QualityReportDetail | JSONResponse:
    try:
        return quality_detail(db, dataset_id)
    except QualityReportNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


@router.get("/datasets/{dataset_id}/quality/history", response_model=QualityHistoryResponse)
def history(dataset_id: str, db: Db) -> QualityHistoryResponse:
    return quality_history(db, dataset_id)


@router.get("/datasets/{dataset_id}/quality/findings", response_model=QualityFindingListResponse)
def findings(
    dataset_id: str,
    db: Db,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    severity: str | None = None,
    blocking: bool | None = None,
    column: str | None = None,
) -> QualityFindingListResponse | JSONResponse:
    try:
        return quality_findings(db, dataset_id, page, page_size, category, severity, blocking, column)
    except (QualityReportNotFoundError, ValueError) as exc:
        return JSONResponse(
            status_code=404 if isinstance(exc, QualityReportNotFoundError) else 422, content={"detail": str(exc)}
        )
