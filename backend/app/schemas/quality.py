from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class QualityRuleDefinition(BaseModel):
    code: str
    category: str
    title: str
    description: str


class QualityAnalysisRequest(BaseModel):
    force_reanalyze: bool = True
    full_scan: bool = False
    notes: str | None = Field(default=None, max_length=500)


class QualityDimensionScores(BaseModel):
    completeness: float
    uniqueness: float
    validity: float
    consistency: float
    temporal: float
    integrity: float
    leakage_safety: float


class QualityFindingResponse(BaseModel):
    id: str
    rule_code: str
    category: str
    severity: Literal["blocker", "error", "warning", "info"]
    title: str
    description: str
    affected_column: str | None
    related_columns: list[str]
    affected_row_count: int | None
    affected_ratio: float | None
    sample_row_indices: list[int]
    evidence: dict[str, Any]
    threshold: dict[str, Any]
    recommendation: str
    blocking: bool
    confidence: float


class QualityReportDetail(BaseModel):
    id: str
    dataset_id: str
    dataset_filename: str
    report_version: int
    schema_version: int
    quality_engine_version: str
    status: str
    readiness_status: str
    overall_score: float
    dimension_scores: QualityDimensionScores
    total_findings: int
    blocker_count: int
    error_count: int
    warning_count: int
    info_count: int
    scanned_rows: int
    total_rows: int
    scan_coverage_ratio: float
    analyzed_columns: int
    created_at: datetime
    completed_at: datetime | None
    duration_ms: int
    summary: dict[str, Any]
    recommendations: list[dict[str, Any]]
    findings: list[QualityFindingResponse]


class QualityHistoryItem(BaseModel):
    id: str
    report_version: int
    schema_version: int
    status: str
    readiness_status: str
    overall_score: float
    blocker_count: int
    created_at: datetime


class QualityHistoryResponse(BaseModel):
    items: list[QualityHistoryItem]


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class QualityFindingListResponse(BaseModel):
    items: list[QualityFindingResponse]
    pagination: PaginationMetadata


class QualityRuleListResponse(BaseModel):
    items: list[QualityRuleDefinition]


class QualityStatsResponse(BaseModel):
    datasets_not_analyzed: int
    blocked_datasets: int
    needs_attention: int
    conditionally_ready: int
    quality_ready: int
    total_blockers: int
    average_quality_score: float | None
