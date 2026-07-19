import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Explanation(Base):
    __tablename__ = "explanations"
    __table_args__ = (Index("ix_explanation_model_type", "model_run_id", "explanation_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    explanation_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # global_feature_importance, local_feature_attribution, etc.
    model_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_model_runs.id", ondelete="CASCADE"), index=True)
    prediction_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    experiment_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    method: Mapped[str] = mapped_column(String(50))  # e.g. tree_shap, permutation, pdp
    method_version: Mapped[str] = mapped_column(String(20))
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    status: Mapped[str] = mapped_column(String(20), default="completed")  # pending, processing, completed, failed
    reliability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    limitations_json: Mapped[list[str]] = mapped_column(JSON, default=list)

    artifact_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    runtime_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_run_id: Mapped[str] = mapped_column(ForeignKey("forecast_model_runs.id", ondelete="CASCADE"), index=True)

    baseline_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    assumptions_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    changes_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, running, completed, failed
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type: Mapped[str] = mapped_column(
        String(50), index=True
    )  # residual_analysis, anomaly, drift, model_disagreement
    model_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("forecast_model_runs.id", ondelete="CASCADE"), nullable=True
    )

    findings_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    artifact_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
