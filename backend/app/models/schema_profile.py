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


class SchemaStatus(StrEnum):
    pending = "pending"
    inferred = "inferred"
    needs_review = "needs_review"
    confirmed = "confirmed"
    superseded = "superseded"
    failed = "failed"


class PhysicalType(StrEnum):
    integer = "integer"
    float = "float"
    boolean = "boolean"
    date = "date"
    datetime = "datetime"
    categorical = "categorical"
    identifier = "identifier"
    text = "text"
    empty = "empty"
    mixed = "mixed"
    unknown = "unknown"


class ConfirmationStatus(StrEnum):
    proposed = "proposed"
    confirmed = "confirmed"
    manually_overridden = "manually_overridden"
    rejected = "rejected"
    unresolved = "unresolved"


class DecisionSource(StrEnum):
    deterministic_inference = "deterministic_inference"
    user_confirmation = "user_confirmation"
    user_override = "user_override"
    system_default = "system_default"


class DatasetSchemaProfile(Base):
    __tablename__ = "dataset_schema_profiles"
    __table_args__ = (
        UniqueConstraint("dataset_id", "schema_version"),
        Index("ix_schema_dataset_status", "dataset_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    schema_version: Mapped[int] = mapped_column(Integer)
    inference_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[SchemaStatus] = mapped_column(Enum(SchemaStatus), index=True)
    total_columns: Mapped[int] = mapped_column(Integer)
    mapped_columns: Mapped[int] = mapped_column(Integer)
    confirmed_columns: Mapped[int] = mapped_column(Integer, default=0)
    unresolved_columns: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_type: Mapped[str] = mapped_column(String(30), default="system")
    profile_summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    warnings_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    configuration_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_checksum: Mapped[str] = mapped_column(String(64))
    sample_row_count: Mapped[int] = mapped_column(Integer)
    rerun_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    columns: Mapped[list["DatasetColumnProfile"]] = relationship(
        back_populates="schema_profile", cascade="all, delete-orphan", order_by="DatasetColumnProfile.column_index"
    )


class DatasetColumnProfile(Base):
    __tablename__ = "dataset_column_profiles"
    __table_args__ = (UniqueConstraint("schema_profile_id", "column_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schema_profile_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_schema_profiles.id", ondelete="CASCADE"), index=True
    )
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    column_index: Mapped[int] = mapped_column(Integer)
    column_name: Mapped[str] = mapped_column(String(255))
    normalized_column_name: Mapped[str] = mapped_column(String(255))
    physical_type: Mapped[PhysicalType] = mapped_column(Enum(PhysicalType))
    semantic_role: Mapped[str] = mapped_column(String(50))
    confidence_score: Mapped[float] = mapped_column(Float)
    confirmation_status: Mapped[ConfirmationStatus] = mapped_column(Enum(ConfirmationStatus))
    decision_source: Mapped[DecisionSource] = mapped_column(Enum(DecisionSource))
    nullable: Mapped[bool] = mapped_column(Boolean)
    null_count: Mapped[int] = mapped_column(Integer)
    sample_count: Mapped[int] = mapped_column(Integer)
    unique_count: Mapped[int] = mapped_column(Integer)
    parse_success_rate: Mapped[float] = mapped_column(Float)
    numeric_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    numeric_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    numeric_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    date_min: Mapped[str | None] = mapped_column(String(40), nullable=True)
    date_max: Mapped[str | None] = mapped_column(String(40), nullable=True)
    string_min_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    string_max_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_values_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    alternatives_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    warnings_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    schema_profile: Mapped[DatasetSchemaProfile] = relationship(back_populates="columns")


class SchemaMappingAudit(Base):
    __tablename__ = "schema_mapping_audits"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    schema_profile_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_schema_profiles.id", ondelete="CASCADE"), index=True
    )
    column_profile_id: Mapped[str | None] = mapped_column(
        ForeignKey("dataset_column_profiles.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(50))
    schema_version: Mapped[int] = mapped_column(Integer)
    column_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    old_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
