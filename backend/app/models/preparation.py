import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PreparationStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    superseded = "superseded"


class PreparationReadiness(StrEnum):
    configuration_required = "configuration_required"
    preparing = "preparing"
    review_required = "review_required"
    model_ready = "model_ready"
    blocked = "blocked"


class PreparedDataset(Base):
    __tablename__ = "prepared_datasets"
    __table_args__ = (
        UniqueConstraint("source_dataset_id", "preparation_version"),
        Index("ix_prepared_source_status", "source_dataset_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    source_schema_profile_id: Mapped[str] = mapped_column(ForeignKey("dataset_schema_profiles.id"), index=True)
    source_quality_report_id: Mapped[str] = mapped_column(ForeignKey("dataset_quality_reports.id"), index=True)
    preparation_version: Mapped[int] = mapped_column(Integer)
    preparation_engine_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[PreparationStatus] = mapped_column(Enum(PreparationStatus), index=True)
    readiness_status: Mapped[PreparationReadiness] = mapped_column(Enum(PreparationReadiness), index=True)
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    configuration_hash: Mapped[str] = mapped_column(String(64))
    source_checksum: Mapped[str] = mapped_column(String(64))
    prepared_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    storage_key: Mapped[str] = mapped_column(String(255), default="")
    artifact_format: Mapped[str] = mapped_column(String(20), default="csv")
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    column_count: Mapped[int] = mapped_column(Integer, default=0)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    target_column: Mapped[str] = mapped_column(String(255))
    date_column: Mapped[str] = mapped_column(String(255))
    group_columns_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    frequency: Mapped[str] = mapped_column(String(20))
    forecast_horizon: Mapped[int] = mapped_column(Integer)
    train_start: Mapped[str | None] = mapped_column(String(40), nullable=True)
    train_end: Mapped[str | None] = mapped_column(String(40), nullable=True)
    validation_start: Mapped[str | None] = mapped_column(String(40), nullable=True)
    validation_end: Mapped[str | None] = mapped_column(String(40), nullable=True)
    test_start: Mapped[str | None] = mapped_column(String(40), nullable=True)
    test_end: Mapped[str | None] = mapped_column(String(40), nullable=True)
    train_rows: Mapped[int] = mapped_column(Integer, default=0)
    validation_rows: Mapped[int] = mapped_column(Integer, default=0)
    test_rows: Mapped[int] = mapped_column(Integer, default=0)
    dropped_rows: Mapped[int] = mapped_column(Integer, default=0)
    generated_rows: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    warnings_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    features: Mapped[list["PreparedFeature"]] = relationship(cascade="all, delete-orphan")
    events: Mapped[list["PreparationEvent"]] = relationship(cascade="all, delete-orphan")


class PreparedFeature(Base):
    __tablename__ = "prepared_features"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prepared_dataset_id: Mapped[str] = mapped_column(ForeignKey("prepared_datasets.id", ondelete="CASCADE"), index=True)
    feature_name: Mapped[str] = mapped_column(String(255))
    source_columns_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    feature_type: Mapped[str] = mapped_column(String(40))
    transformation_type: Mapped[str] = mapped_column(String(50))
    semantic_role: Mapped[str] = mapped_column(String(50), default="unknown")
    physical_type: Mapped[str] = mapped_column(String(30))
    availability_type: Mapped[str] = mapped_column(String(40))
    leakage_risk: Mapped[str] = mapped_column(String(30), default="none")
    included: Mapped[bool] = mapped_column(default=True)
    generated: Mapped[bool] = mapped_column(default=False)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    lineage_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PreparationEvent(Base):
    __tablename__ = "preparation_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prepared_dataset_id: Mapped[str] = mapped_column(ForeignKey("prepared_datasets.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
