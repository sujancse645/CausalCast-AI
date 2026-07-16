import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from typing import cast

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.exceptions import (
    ColumnProfileNotFoundError,
    DatasetNotReadyForSchemaError,
    DatasetSchemaNotFoundError,
    SchemaConfirmationError,
    SchemaInferenceError,
)
from app.models.dataset import Dataset, DatasetStatus
from app.models.schema_profile import (
    ConfirmationStatus,
    DatasetColumnProfile,
    DatasetSchemaProfile,
    DecisionSource,
    SchemaMappingAudit,
    SchemaStatus,
)
from app.schemas.schema_mapping import (
    ColumnCandidate,
    ColumnEvidence,
    ColumnMappingUpdateResponse,
    ColumnProfileResponse,
    DatasetSchemaDetail,
    DatasetSchemaSummary,
    SchemaConfirmationResponse,
    SchemaHistoryItem,
    SchemaHistoryResponse,
    SchemaStatsResponse,
    SchemaValidationIssue,
)
from app.services.column_profiler import PhysicalProfile, scan_csv
from app.services.dataset_storage_service import DatasetStorageService
from app.services.semantic_role_registry import SemanticRole
from app.services.semantic_role_rules import Candidate, candidates

logger = logging.getLogger(__name__)
DIMENSIONS = {
    "channel",
    "campaign",
    "customer_id",
    "product_id",
    "product_category",
    "country",
    "region",
    "city",
    "device",
    "source",
    "medium",
}
METRICS = {
    "revenue",
    "spend",
    "impressions",
    "clicks",
    "conversions",
    "orders",
    "units_sold",
    "roas",
    "ctr",
    "cpc",
    "cpa",
    "conversion_rate",
}
TARGETS = {"revenue", "conversions", "orders", "units_sold", "target"}


def _raw_path(dataset: Dataset, settings: Settings) -> Path:
    storage = DatasetStorageService(settings)
    path = (storage.upload_dir / dataset.stored_filename).resolve()
    if path.parent != storage.upload_dir or not path.is_file():
        raise DatasetNotReadyForSchemaError("Dataset raw file is unavailable")
    return path


def _issues(roles: list[tuple[str, str, float, bool]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    blocking: list[dict[str, object]] = []
    warnings: list[dict[str, object]] = []
    mapped = [r for _, r, _, _ in roles if r not in {"unknown", "ignored"}]
    dates = [n for n, r, _, _ in roles if r in {"date", "timestamp"}]
    targets = [n for n, r, _, _ in roles if r in TARGETS]
    if not dates:
        blocking.append(
            {
                "code": "missing_date",
                "message": "No plausible date or timestamp mapping is available.",
                "severity": "blocking",
                "column_names": [],
            }
        )
    if not targets:
        blocking.append(
            {
                "code": "missing_target",
                "message": "No plausible target metric is available.",
                "severity": "blocking",
                "column_names": [],
            }
        )
    revenues = [n for n, r, c, _ in roles if r == "revenue" and c >= 0.75]
    if len(revenues) > 1:
        warnings.append(
            {
                "code": "duplicate_revenue",
                "message": "Multiple strong revenue candidates require review.",
                "severity": "warning",
                "column_names": revenues,
            }
        )
    if "spend" in mapped and "revenue" not in mapped:
        warnings.append(
            {
                "code": "spend_without_revenue",
                "message": "Spend exists without a revenue mapping.",
                "severity": "warning",
                "column_names": [],
            }
        )
    return blocking, warnings


def _summary(columns: list[DatasetColumnProfile]) -> dict[str, object]:
    roles = [
        (c.column_name, c.semantic_role, c.confidence_score, c.confirmation_status == ConfirmationStatus.unresolved)
        for c in columns
    ]
    blocking, warnings = _issues(roles)
    unresolved = sum(c.semantic_role == "unknown" for c in columns)
    ambiguous = sum(bool(c.warnings_json) for c in columns)

    def first(role_set: set[str]) -> str | None:
        return next((c.column_name for c in columns if c.semantic_role in role_set), None)

    mapped = sum(c.semantic_role not in {"unknown", "ignored"} for c in columns)
    confirmed = sum(
        c.confirmation_status in {ConfirmationStatus.confirmed, ConfirmationStatus.manually_overridden} for c in columns
    )
    return {
        "total_columns": len(columns),
        "mapped_columns": mapped,
        "confirmed_columns": confirmed,
        "unresolved_columns": unresolved,
        "ambiguous_columns": ambiguous,
        "average_confidence": round(sum(c.confidence_score for c in columns) / max(len(columns), 1), 4),
        "primary_date_candidate": first({"date", "timestamp"}),
        "primary_target_candidate": first(TARGETS),
        "revenue_candidate": first({"revenue"}),
        "spend_candidate": first({"spend"}),
        "available_marketing_dimensions": [c.column_name for c in columns if c.semantic_role in DIMENSIONS],
        "available_performance_metrics": [c.column_name for c in columns if c.semantic_role in METRICS],
        "blocking_issues": blocking,
        "warnings": warnings,
        "readiness_status": "needs_review" if blocking or unresolved or ambiguous else "mapping_ready",
    }


def _column(
    profile: PhysicalProfile, ranked: list[Candidate], settings: Settings, dataset_id: str, schema_id: str
) -> DatasetColumnProfile:
    top = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None
    ambiguous = bool(top and second and top.score - second.score < settings.schema_inference_ambiguity_margin)
    role = (
        top.role.value if top and top.score >= settings.schema_inference_min_confidence and not ambiguous else "unknown"
    )
    confidence = top.score if top else 0.0
    warnings = []
    if ambiguous:
        warnings.append(
            {
                "code": "ambiguous_candidates",
                "message": "Top semantic candidates are too close.",
                "severity": "warning",
                "column_names": [profile.column_name],
            }
        )
    if top and top.role in {SemanticRole.date, SemanticRole.timestamp} and profile.parse_success_rate < 0.8:
        warnings.append(
            {
                "code": "low_date_parse_rate",
                "message": "Date parse rate is below 80%.",
                "severity": "warning",
                "column_names": [profile.column_name],
            }
        )
    return DatasetColumnProfile(
        schema_profile_id=schema_id,
        dataset_id=dataset_id,
        column_index=profile.column_index,
        column_name=profile.column_name,
        normalized_column_name=profile.normalized_name,
        physical_type=profile.physical_type,
        semantic_role=role,
        confidence_score=confidence,
        confirmation_status=ConfirmationStatus.unresolved if role == "unknown" else ConfirmationStatus.proposed,
        decision_source=DecisionSource.deterministic_inference,
        nullable=profile.nullable,
        null_count=profile.null_count,
        sample_count=profile.sample_count,
        unique_count=profile.unique_count,
        parse_success_rate=profile.parse_success_rate,
        numeric_min=profile.numeric_min,
        numeric_max=profile.numeric_max,
        numeric_mean=profile.numeric_mean,
        date_min=profile.date_min,
        date_max=profile.date_max,
        string_min_length=profile.string_min_length,
        string_max_length=profile.string_max_length,
        sample_values_json=profile.sample_values,
        evidence_json=top.evidence if top else [],
        alternatives_json=[
            {
                "role": item.role.value,
                "confidence_score": item.score,
                "summary_evidence": [str(e["description"]) for e in item.evidence],
            }
            for item in ranked[:3]
        ],
        warnings_json=warnings,
    )


def _relationship_evidence(columns: list[DatasetColumnProfile], rows: list[dict[str, str]]) -> None:
    by_role = {column.semantic_role: column for column in columns if column.semantic_role != "unknown"}
    relationships = {
        "roas": ("revenue", "spend"),
        "ctr": ("clicks", "impressions"),
        "cpc": ("spend", "clicks"),
        "cpa": ("spend", "conversions"),
        "conversion_rate": ("conversions", "clicks"),
    }
    for metric, (numerator, denominator) in relationships.items():
        if not {metric, numerator, denominator} <= by_role.keys():
            continue
        matches = observed = 0
        for row in rows:
            try:
                actual = float(row[by_role[metric].column_name])
                top = float(row[by_role[numerator].column_name])
                bottom = float(row[by_role[denominator].column_name])
                if bottom == 0:
                    continue
                expected = top / bottom
                observed += 1
                matches += abs(actual - expected) <= max(abs(expected) * 0.25, 0.02)
            except (KeyError, TypeError, ValueError):
                continue
        if observed:
            rate = matches / observed
            contribution = 0.05 if rate >= 0.7 else -0.05
            target = by_role[metric]
            target.evidence_json.append(
                {
                    "evidence_type": "relationship",
                    "description": f"Approximately matches {numerator} / {denominator} in sampled rows",
                    "score_contribution": contribution,
                    "observed_value": round(rate, 3),
                    "expected_pattern": ">= 0.7 agreement",
                    "severity": "info" if contribution > 0 else "warning",
                }
            )
            target.confidence_score = round(max(0.0, min(1.0, target.confidence_score + contribution)), 4)


def infer_schema(db: Session, dataset_id: str, settings: Settings, reason: str | None = None) -> DatasetSchemaDetail:
    started = monotonic()
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise DatasetSchemaNotFoundError("Dataset was not found")
    if dataset.status != DatasetStatus.ready:
        raise DatasetNotReadyForSchemaError("Only active ready datasets can be inferred")
    path = _raw_path(dataset, settings)
    profiles, rows = scan_csv(
        path,
        dataset.encoding or "utf-8-sig",
        dataset.delimiter or ",",
        settings.schema_inference_sample_rows,
        settings.schema_inference_preview_values,
        settings.schema_inference_max_unique_tracking,
    )
    latest = (
        db.scalar(
            select(func.max(DatasetSchemaProfile.schema_version)).where(DatasetSchemaProfile.dataset_id == dataset_id)
        )
        or 0
    )
    db.execute(
        update(DatasetSchemaProfile)
        .where(
            DatasetSchemaProfile.dataset_id == dataset_id,
            DatasetSchemaProfile.status.in_([SchemaStatus.inferred, SchemaStatus.needs_review, SchemaStatus.confirmed]),
        )
        .values(status=SchemaStatus.superseded)
    )
    schema_id = str(__import__("uuid").uuid4())
    columns = [_column(p, candidates(p), settings, dataset_id, schema_id) for p in profiles]
    _relationship_evidence(columns, rows)
    summary = _summary(columns)
    config: dict[str, object] = {
        "sample_rows": settings.schema_inference_sample_rows,
        "min_confidence": settings.schema_inference_min_confidence,
        "ambiguity_margin": settings.schema_inference_ambiguity_margin,
    }
    config["hash"] = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    schema = DatasetSchemaProfile(
        id=schema_id,
        dataset_id=dataset_id,
        schema_version=latest + 1,
        inference_version=settings.schema_inference_version,
        status=SchemaStatus.needs_review,
        total_columns=len(columns),
        mapped_columns=cast(int, summary["mapped_columns"]),
        confirmed_columns=0,
        unresolved_columns=cast(int, summary["unresolved_columns"]),
        profile_summary_json=summary,
        warnings_json=cast(list[dict[str, object]], summary["warnings"]),
        configuration_json=config,
        source_checksum=dataset.checksum_sha256,
        sample_row_count=min(dataset.row_count, settings.schema_inference_sample_rows),
        rerun_reason=reason,
        columns=columns,
    )
    try:
        db.add(schema)
        db.commit()
        db.refresh(schema)
    except Exception as exc:
        db.rollback()
        raise SchemaInferenceError("Schema inference could not be persisted") from exc
    logger.info(
        "schema_inference_completed dataset_id=%s schema_version=%s columns=%s duration_ms=%s",
        dataset_id,
        schema.schema_version,
        len(columns),
        round((monotonic() - started) * 1000),
    )
    return schema_detail(db, dataset_id)


def _column_response(c: DatasetColumnProfile) -> ColumnProfileResponse:
    data = {name: getattr(c, name) for name in ColumnProfileResponse.model_fields if hasattr(c, name)}
    data.update(
        sample_values=c.sample_values_json,
        evidence=[ColumnEvidence.model_validate(x) for x in c.evidence_json],
        alternatives=[ColumnCandidate.model_validate(x) for x in c.alternatives_json],
        warnings=[SchemaValidationIssue.model_validate(x) for x in c.warnings_json],
    )
    return ColumnProfileResponse.model_validate(data)


def schema_detail(db: Session, dataset_id: str) -> DatasetSchemaDetail:
    schema = db.scalar(
        select(DatasetSchemaProfile)
        .options(selectinload(DatasetSchemaProfile.columns))
        .where(DatasetSchemaProfile.dataset_id == dataset_id, DatasetSchemaProfile.status != SchemaStatus.superseded)
        .order_by(DatasetSchemaProfile.schema_version.desc())
    )
    if schema is None:
        raise DatasetSchemaNotFoundError("Dataset schema has not been inferred")
    dataset = db.get(Dataset, dataset_id)
    assert dataset is not None
    return DatasetSchemaDetail(
        id=schema.id,
        dataset_id=dataset_id,
        dataset_filename=dataset.original_filename,
        dataset_row_count=dataset.row_count,
        dataset_column_count=dataset.column_count,
        schema_version=schema.schema_version,
        inference_version=schema.inference_version,
        status=schema.status.value,
        created_at=schema.created_at,
        updated_at=schema.updated_at,
        confirmed_at=schema.confirmed_at,
        source_checksum=schema.source_checksum,
        sample_row_count=schema.sample_row_count,
        summary=DatasetSchemaSummary.model_validate(schema.profile_summary_json),
        columns=[_column_response(c) for c in schema.columns],
    )


def schema_history(db: Session, dataset_id: str) -> SchemaHistoryResponse:
    items = db.scalars(
        select(DatasetSchemaProfile)
        .where(DatasetSchemaProfile.dataset_id == dataset_id)
        .order_by(DatasetSchemaProfile.schema_version.desc())
    ).all()
    return SchemaHistoryResponse(items=[SchemaHistoryItem.model_validate(x, from_attributes=True) for x in items])


def update_mapping(
    db: Session, dataset_id: str, column_id: str, role: str, reason: str | None
) -> ColumnMappingUpdateResponse:
    if role not in {r.value for r in SemanticRole}:
        raise ValueError("Invalid semantic role")
    schema = db.scalar(
        select(DatasetSchemaProfile)
        .options(selectinload(DatasetSchemaProfile.columns))
        .where(DatasetSchemaProfile.dataset_id == dataset_id, DatasetSchemaProfile.status != SchemaStatus.superseded)
        .order_by(DatasetSchemaProfile.schema_version.desc())
    )
    if schema is None:
        raise DatasetSchemaNotFoundError("Dataset schema has not been inferred")
    column = next((c for c in schema.columns if c.id == column_id), None)
    if column is None:
        raise ColumnProfileNotFoundError("Column profile was not found")
    old = column.semantic_role
    column.semantic_role = role
    column.confirmation_status = ConfirmationStatus.manually_overridden
    column.decision_source = DecisionSource.user_override
    column.confidence_score = 1.0
    db.add(
        SchemaMappingAudit(
            schema_profile_id=schema.id,
            column_profile_id=column.id,
            action_type="manual_override",
            schema_version=schema.schema_version,
            column_name=column.column_name,
            old_role=old,
            new_role=role,
            source="local_user",
            reason=reason,
        )
    )
    summary = _summary(schema.columns)
    schema.profile_summary_json = summary
    schema.mapped_columns = cast(int, summary["mapped_columns"])
    schema.confirmed_columns = cast(int, summary["confirmed_columns"])
    schema.unresolved_columns = cast(int, summary["unresolved_columns"])
    db.commit()
    return ColumnMappingUpdateResponse(
        column=_column_response(column), summary=DatasetSchemaSummary.model_validate(summary)
    )


def confirm_schema(db: Session, dataset_id: str) -> SchemaConfirmationResponse:
    schema = db.scalar(
        select(DatasetSchemaProfile)
        .options(selectinload(DatasetSchemaProfile.columns))
        .where(DatasetSchemaProfile.dataset_id == dataset_id, DatasetSchemaProfile.status != SchemaStatus.superseded)
        .order_by(DatasetSchemaProfile.schema_version.desc())
    )
    if schema is None:
        raise DatasetSchemaNotFoundError("Dataset schema has not been inferred")
    summary = _summary(schema.columns)
    issues = [str(x["message"]) for x in cast(list[dict[str, object]], summary["blocking_issues"])]
    if issues:
        raise SchemaConfirmationError(issues)
    now = datetime.now(UTC)
    for c in schema.columns:
        if c.semantic_role == "unknown":
            raise SchemaConfirmationError([f"Column {c.column_name} must be mapped or ignored"])
        if c.confirmation_status == ConfirmationStatus.proposed:
            c.confirmation_status = ConfirmationStatus.confirmed
            c.decision_source = DecisionSource.user_confirmation
    summary = _summary(schema.columns)
    summary["readiness_status"] = "confirmed"
    schema.profile_summary_json = summary
    schema.status = SchemaStatus.confirmed
    schema.confirmed_at = now
    schema.confirmed_columns = len(schema.columns)
    schema.unresolved_columns = 0
    db.add(
        SchemaMappingAudit(
            schema_profile_id=schema.id,
            action_type="schema_confirmed",
            schema_version=schema.schema_version,
            source="local_user",
        )
    )
    db.commit()
    return SchemaConfirmationResponse(
        dataset_id=dataset_id,
        schema_profile_id=schema.id,
        schema_version=schema.schema_version,
        status="confirmed",
        confirmed_at=now,
        summary=DatasetSchemaSummary.model_validate(summary),
    )


def schema_stats(db: Session) -> SchemaStatsResponse:
    awaiting = (
        db.scalar(
            select(func.count())
            .select_from(DatasetSchemaProfile)
            .where(DatasetSchemaProfile.status == SchemaStatus.needs_review)
        )
        or 0
    )
    confirmed = (
        db.scalar(
            select(func.count())
            .select_from(DatasetSchemaProfile)
            .where(DatasetSchemaProfile.status == SchemaStatus.confirmed)
        )
        or 0
    )
    unresolved = (
        db.scalar(
            select(func.coalesce(func.sum(DatasetSchemaProfile.unresolved_columns), 0)).where(
                DatasetSchemaProfile.status == SchemaStatus.needs_review
            )
        )
        or 0
    )
    return SchemaStatsResponse(awaiting_review=awaiting, confirmed_schemas=confirmed, unresolved_columns=unresolved)
