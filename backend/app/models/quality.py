import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class QualityReportStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    superseded = "superseded"


class QualityReadiness(StrEnum):
    not_analyzed = "not_analyzed"
    blocked = "blocked"
    needs_attention = "needs_attention"
    conditionally_ready = "conditionally_ready"
    quality_ready = "quality_ready"


class QualitySeverity(StrEnum):
    blocker = "blocker"
    error = "error"
    warning = "warning"
    info = "info"


class DatasetQualityReport(Base):
    __tablename__ = "dataset_quality_reports"
    __table_args__ = (
        UniqueConstraint("dataset_id", "report_version"),
        Index("ix_quality_dataset_status", "dataset_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    schema_profile_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_schema_profiles.id", ondelete="CASCADE"), index=True
    )
    report_version: Mapped[int] = mapped_column(Integer)
    quality_engine_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[QualityReportStatus] = mapped_column(Enum(QualityReportStatus), index=True)
    readiness_status: Mapped[QualityReadiness] = mapped_column(Enum(QualityReadiness), index=True)
    overall_score: Mapped[float] = mapped_column(Float, default=0)
    completeness_score: Mapped[float] = mapped_column(Float, default=100)
    validity_score: Mapped[float] = mapped_column(Float, default=100)
    consistency_score: Mapped[float] = mapped_column(Float, default=100)
    uniqueness_score: Mapped[float] = mapped_column(Float, default=100)
    temporal_score: Mapped[float] = mapped_column(Float, default=100)
    integrity_score: Mapped[float] = mapped_column(Float, default=100)
    leakage_safety_score: Mapped[float] = mapped_column(Float, default=100)
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    blocker_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, default=0)
    info_count: Mapped[int] = mapped_column(Integer, default=0)
    scanned_rows: Mapped[int] = mapped_column(Integer)
    total_rows: Mapped[int] = mapped_column(Integer)
    scan_coverage_ratio: Mapped[float] = mapped_column(Float)
    analyzed_columns: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dataset_checksum: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[int] = mapped_column(Integer)
    configuration_hash: Mapped[str] = mapped_column(String(64))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    recommendations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    findings: Mapped[list["DatasetQualityFinding"]] = relationship(
        cascade="all, delete-orphan", order_by="DatasetQualityFinding.created_at"
    )


class DatasetQualityFinding(Base):
    __tablename__ = "dataset_quality_findings"
    __table_args__ = (Index("ix_quality_finding_filter", "quality_report_id", "category", "severity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quality_report_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_quality_reports.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    rule_code: Mapped[str] = mapped_column(String(50), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[QualitySeverity] = mapped_column(Enum(QualitySeverity), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    affected_column: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    related_columns_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    affected_row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    affected_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sample_row_indices_json: Mapped[list[int]] = mapped_column(JSON, default=list)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    threshold_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    recommendation: Mapped[str] = mapped_column(Text)
    blocking: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
