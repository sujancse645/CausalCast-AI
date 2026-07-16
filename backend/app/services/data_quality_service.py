import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from statistics import median, quantiles
from time import monotonic
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.exceptions import (
    DatasetNotReadyForQualityAnalysisError,
    MissingConfirmedSchemaError,
    QualityReportNotFoundError,
)
from app.models.dataset import Dataset, DatasetStatus
from app.models.quality import (
    DatasetQualityFinding,
    DatasetQualityReport,
    QualityReadiness,
    QualityReportStatus,
    QualitySeverity,
)
from app.models.schema_profile import DatasetColumnProfile, DatasetSchemaProfile, SchemaStatus
from app.schemas.quality import (
    PaginationMetadata,
    QualityDimensionScores,
    QualityFindingListResponse,
    QualityFindingResponse,
    QualityHistoryItem,
    QualityHistoryResponse,
    QualityReportDetail,
    QualityStatsResponse,
)
from app.services.dataset_storage_service import DatasetStorageService
from app.services.quality_scan_service import QualityScan, parse_date, parse_number, scan_csv
from app.services.quality_scoring import score

logger = logging.getLogger(__name__)
NUMERIC_ROLES = {
    "revenue",
    "spend",
    "cost",
    "price",
    "profit",
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
    "target",
}
COUNT_ROLES = {"impressions", "clicks", "conversions", "orders", "units_sold"}
TARGET_ROLES = {"revenue", "conversions", "orders", "units_sold", "profit", "target"}
DIMENSION_ROLES = {"channel", "campaign", "product_category", "country", "region", "city", "device", "source", "medium"}


def _finding(
    code: str,
    category: str,
    severity: str,
    title: str,
    description: str,
    recommendation: str,
    *,
    column: str | None = None,
    columns: list[str] | None = None,
    count: int | None = None,
    ratio: float | None = None,
    rows: list[int] | None = None,
    evidence: dict[str, Any] | None = None,
    threshold: dict[str, Any] | None = None,
    blocking: bool = False,
    confidence: float = 1.0,
) -> dict[str, Any]:
    return {
        "rule_code": code,
        "category": category,
        "severity": severity,
        "title": title,
        "description": description,
        "affected_column": column,
        "related_columns": columns or [],
        "affected_row_count": count,
        "affected_ratio": ratio,
        "sample_row_indices": rows or [],
        "evidence": evidence or {},
        "threshold": threshold or {},
        "recommendation": recommendation,
        "blocking": blocking,
        "confidence": confidence,
    }


def _raw_path(dataset: Dataset, settings: Settings) -> Path:
    storage = DatasetStorageService(settings)
    path = (storage.upload_dir / dataset.stored_filename).resolve()
    if path.parent != storage.upload_dir or not path.is_file():
        raise DatasetNotReadyForQualityAnalysisError("Dataset raw file is unavailable")
    return path


def _active_schema(db: Session, dataset_id: str) -> DatasetSchemaProfile:
    schema = db.scalar(
        select(DatasetSchemaProfile)
        .options(selectinload(DatasetSchemaProfile.columns))
        .where(
            DatasetSchemaProfile.dataset_id == dataset_id,
            DatasetSchemaProfile.status.not_in([SchemaStatus.superseded, SchemaStatus.failed]),
        )
        .order_by(DatasetSchemaProfile.schema_version.desc())
    )
    if schema is None:
        raise MissingConfirmedSchemaError("Run and review schema inference before quality analysis")
    return schema


def evaluate(
    scan: QualityScan, schema: DatasetSchemaProfile, settings: Settings
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    roles: dict[str, str] = {}
    for column in schema.columns:
        if column.semantic_role not in {"unknown", "ignored"}:
            roles.setdefault(column.semantic_role, column.column_name)
    by_name = {column.column_name: column for column in schema.columns if column.semantic_role != "ignored"}
    total = max(scan.scanned_rows, 1)
    if schema.status != SchemaStatus.confirmed:
        findings.append(
            _finding(
                "DQ_SCHEMA_001",
                "schema",
                "warning",
                "Schema mapping requires review",
                "Quality analysis used a schema that has not been fully confirmed.",
                "Confirm or override schema mappings before downstream preparation.",
                confidence=1.0,
            )
        )
    if not any(role in roles for role in TARGET_ROLES):
        findings.append(
            _finding(
                "DQ_SCHEMA_002",
                "schema",
                "blocker",
                "Target mapping is missing",
                "No mapped target metric is available.",
                "Map and confirm a target metric.",
                blocking=True,
            )
        )
    if not any(role in roles for role in {"date", "timestamp"}):
        findings.append(
            _finding(
                "DQ_SCHEMA_003",
                "schema",
                "blocker",
                "Primary date mapping is missing",
                "No mapped date or timestamp is available.",
                "Map and confirm the primary time column.",
                blocking=True,
            )
        )
    for name, mapped in by_name.items():
        profile = scan.columns.get(name)
        if profile is None:
            continue
        ratio = profile.missing / total
        critical = mapped.semantic_role in TARGET_ROLES | {"date", "timestamp"}
        if profile.missing:
            if ratio >= settings.data_quality_missing_blocker_threshold and critical:
                severity, blocking = "blocker", True
            elif ratio >= settings.data_quality_missing_error_threshold:
                severity, blocking = "error", False
            elif ratio >= settings.data_quality_missing_warning_threshold:
                severity, blocking = "warning", False
            else:
                severity, blocking = "info", False
            findings.append(
                _finding(
                    "DQ_COMPLETENESS_001",
                    "completeness",
                    severity,
                    "Missing values detected",
                    "Null-like values were observed in a mapped column.",
                    "Review source-system null handling; no values were changed.",
                    column=name,
                    count=profile.missing,
                    ratio=round(ratio, 6),
                    evidence={
                        "observed_count": profile.missing,
                        "observed_ratio": round(ratio, 6),
                        "scan_scope": scan.scanned_rows,
                    },
                    threshold={
                        "warning": settings.data_quality_missing_warning_threshold,
                        "error": settings.data_quality_missing_error_threshold,
                        "blocker": settings.data_quality_missing_blocker_threshold,
                    },
                    blocking=blocking,
                )
            )
        if not profile.values:
            findings.append(
                _finding(
                    "DQ_COMPLETENESS_002",
                    "completeness",
                    "blocker" if critical else "error",
                    "Column is fully empty",
                    "No non-missing values were observed.",
                    "Correct the source or explicitly ignore the column.",
                    column=name,
                    count=scan.scanned_rows,
                    ratio=1.0,
                    blocking=critical,
                )
            )
        unique = len(profile.frequencies)
        if profile.values and unique == 1:
            blocking = mapped.semantic_role in TARGET_ROLES
            findings.append(
                _finding(
                    "DQ_CARDINALITY_001",
                    "cardinality",
                    "blocker" if blocking else "info",
                    "Constant column",
                    "All observed non-missing values are identical.",
                    "Review whether this column carries useful information.",
                    column=name,
                    count=len(profile.values),
                    ratio=1.0,
                    blocking=blocking,
                )
            )
        dominant = max(profile.frequencies.values(), default=0) / max(len(profile.values), 1)
        if unique > 1 and dominant >= settings.data_quality_near_constant_threshold:
            findings.append(
                _finding(
                    "DQ_CARDINALITY_003",
                    "cardinality",
                    "warning",
                    "Near-constant column",
                    "One value dominates the observed column.",
                    "Review modeling usefulness in Phase 2D.",
                    column=name,
                    ratio=dominant,
                    threshold={"dominant_ratio": settings.data_quality_near_constant_threshold},
                )
            )
        unique_ratio = unique / max(len(profile.values), 1)
        if mapped.semantic_role in DIMENSION_ROLES and unique_ratio >= settings.data_quality_high_cardinality_threshold:
            findings.append(
                _finding(
                    "DQ_CARDINALITY_002",
                    "cardinality",
                    "warning",
                    "High-cardinality dimension",
                    "A mapped dimension is near-unique in scanned rows.",
                    "Review grouping granularity before feature engineering.",
                    column=name,
                    ratio=round(unique_ratio, 6),
                    threshold={"unique_ratio": settings.data_quality_high_cardinality_threshold},
                    confidence=0.9,
                )
            )
        if mapped.semantic_role in NUMERIC_ROLES:
            invalid_rows = [
                i + 2
                for i, row in enumerate(scan.rows)
                if row.get(name, "").lower() not in {"", "null", "none", "na", "n/a", "nan", "missing"}
                and parse_number(row[name]) is None
            ]
            if invalid_rows:
                findings.append(
                    _finding(
                        "DQ_VALIDITY_001",
                        "validity",
                        "error",
                        "Numeric type inconsistency",
                        "Some mapped numeric values could not be parsed safely.",
                        "Correct numeric formatting in a derived cleaning phase.",
                        column=name,
                        count=len(invalid_rows),
                        ratio=len(invalid_rows) / total,
                        rows=invalid_rows[: settings.data_quality_evidence_rows],
                        evidence={"parse_failures": len(invalid_rows), "scan_scope": scan.scanned_rows},
                    )
                )
            numbers = [(i + 2, parse_number(row.get(name, ""))) for i, row in enumerate(scan.rows)]
            valid_numbers = [(i, value) for i, value in numbers if value is not None]
            negative = [i for i, value in valid_numbers if value < 0]
            if negative and mapped.semantic_role in COUNT_ROLES | {
                "spend",
                "price",
                "roas",
                "ctr",
                "cpc",
                "cpa",
                "conversion_rate",
            }:
                findings.append(
                    _finding(
                        "DQ_VALIDITY_002",
                        "validity",
                        "error",
                        "Negative metric values",
                        "Negative values were observed for a normally non-negative metric.",
                        "Verify corrections or source-system sign conventions.",
                        column=name,
                        count=len(negative),
                        ratio=len(negative) / total,
                        rows=negative[: settings.data_quality_evidence_rows],
                    )
                )
            if mapped.semantic_role in {"ctr", "conversion_rate"}:
                values = [value for _, value in valid_numbers]
                invalid = [i for i, value in valid_numbers if value < 0 or value > 100]
                mixed = any(0 < value <= 1 for value in values) and any(value > 1 for value in values)
                if invalid or mixed:
                    findings.append(
                        _finding(
                            "DQ_VALIDITY_003",
                            "validity",
                            "error" if invalid else "warning",
                            "Invalid or mixed percentage scale",
                            "Percentage values use an invalid or mixed fraction/percentage scale.",
                            "Standardize scale only in a versioned derived dataset.",
                            column=name,
                            count=len(invalid) or len(values),
                            rows=invalid[: settings.data_quality_evidence_rows],
                            evidence={"mixed_scale": mixed, "invalid_count": len(invalid)},
                        )
                    )
            values_only = [value for _, value in valid_numbers]
            if len(values_only) >= 8 and len(set(values_only)) > 3:
                q1, _, q3 = quantiles(values_only, n=4, method="inclusive")
                iqr = q3 - q1
                if iqr > 0:
                    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    outliers = [i for i, value in valid_numbers if value < low or value > high]
                    if outliers:
                        ratio_out = len(outliers) / len(valid_numbers)
                        severity = "error" if ratio_out >= settings.data_quality_outlier_error_threshold else "warning"
                        findings.append(
                            _finding(
                                "DQ_OUTLIER_001",
                                "outlier",
                                severity,
                                "Robust numeric outliers",
                                "Values fall outside deterministic 1.5×IQR fences; "
                                "this is a review signal, not proof of error.",
                                "Review business context before any derived transformation.",
                                column=name,
                                count=len(outliers),
                                ratio=ratio_out,
                                rows=outliers[: settings.data_quality_evidence_rows],
                                evidence={"method": "IQR", "lower_fence": low, "upper_fence": high},
                                threshold={"multiplier": 1.5},
                                confidence=0.85,
                            )
                        )
    if scan.duplicate_count:
        ratio = scan.duplicate_count / total
        severity = "error" if ratio >= settings.data_quality_duplicate_error_threshold else "warning"
        findings.append(
            _finding(
                "DQ_DUPLICATE_001",
                "uniqueness",
                severity,
                "Exact duplicate rows",
                "Stable row fingerprints repeat within the scan.",
                "Investigate duplicate generation before creating a derived dataset.",
                count=scan.duplicate_count,
                ratio=ratio,
                rows=scan.duplicate_indices,
                evidence={"hash": "sha256", "scan_scope": scan.scanned_rows},
            )
        )
    key_names = [roles[r] for r in ("date", "campaign", "channel") if r in roles]
    if len(key_names) >= 2:
        keys: set[tuple[str, ...]] = set()
        duplicate_key_count = 0
        duplicates: list[int] = []
        for index, row in enumerate(scan.rows, start=2):
            key = tuple(row.get(name, "") for name in key_names)
            if key in keys:
                duplicate_key_count += 1
                if len(duplicates) < settings.data_quality_evidence_rows:
                    duplicates.append(index)
            keys.add(key)
        if duplicates:
            findings.append(
                _finding(
                    "DQ_DUPLICATE_002",
                    "uniqueness",
                    "warning",
                    "Candidate business-key duplicates",
                    "The heuristic date/dimension key repeats; aggregation may make this legitimate.",
                    "Confirm the intended dataset grain.",
                    columns=key_names,
                    count=duplicate_key_count,
                    rows=duplicates,
                    confidence=0.7,
                )
            )
    temporal_summary = _temporal(scan, roles, settings, findings)
    _relationships(scan, roles, settings, findings)
    _leakage(scan, roles, by_name, settings, findings)
    return findings, {
        "temporal": temporal_summary,
        "scan_mode": "full" if scan.scanned_rows < settings.data_quality_max_scan_rows else "bounded",
        "scanned_rows": scan.scanned_rows,
    }


def _temporal(
    scan: QualityScan, roles: dict[str, str], settings: Settings, findings: list[dict[str, Any]]
) -> dict[str, Any]:
    name = roles.get("date") or roles.get("timestamp")
    if not name:
        return {"available": False}
    parsed = [(i + 2, parse_date(row.get(name, ""))) for i, row in enumerate(scan.rows)]
    invalid = [i for i, value in parsed if row_value(scan, i, name) and value is None]
    valid = [(i, value) for i, value in parsed if value is not None]
    if invalid:
        ratio = len(invalid) / max(scan.scanned_rows, 1)
        severity = "blocker" if 1 - ratio < settings.data_quality_date_parse_threshold else "error"
        findings.append(
            _finding(
                "DQ_TEMPORAL_001",
                "temporal",
                severity,
                "Invalid primary dates",
                "Primary-date values failed deterministic parsing.",
                "Correct dates in a versioned derived dataset.",
                column=name,
                count=len(invalid),
                ratio=ratio,
                rows=invalid[: settings.data_quality_evidence_rows],
                blocking=severity == "blocker",
            )
        )
    dates = [value for _, value in valid]
    out_of_order = [valid[i][0] for i in range(1, len(valid)) if valid[i][1] < valid[i - 1][1]]
    if out_of_order:
        findings.append(
            _finding(
                "DQ_TEMPORAL_003",
                "temporal",
                "warning",
                "Dates are out of source order",
                "Primary dates move backward in file order.",
                "Sort only in a derived preparation step.",
                column=name,
                count=len(out_of_order),
                rows=out_of_order[: settings.data_quality_evidence_rows],
            )
        )
    future = [i for i, value in valid if value.date() > datetime.now(UTC).date()]
    if future:
        findings.append(
            _finding(
                "DQ_TEMPORAL_004",
                "temporal",
                "error",
                "Future dates detected",
                "Dates occur after the UTC analysis date.",
                "Verify source timestamps and availability.",
                column=name,
                count=len(future),
                rows=future[: settings.data_quality_evidence_rows],
            )
        )
    unique_dates = sorted(set(dates))
    intervals = [(unique_dates[i] - unique_dates[i - 1]).total_seconds() for i in range(1, len(unique_dates))]
    frequency = "insufficient"
    gaps: list[float] = []
    if intervals:
        dominant = median(intervals)
        frequency = (
            "hourly"
            if dominant <= 5400
            else "daily"
            if dominant <= 129600
            else "weekly"
            if dominant <= 864000
            else "monthly"
            if dominant <= 3888000
            else "quarterly"
            if dominant <= 10368000
            else "irregular"
        )
        gaps = [gap for gap in intervals if gap > dominant * settings.data_quality_temporal_gap_warning_multiplier]
        if gaps:
            findings.append(
                _finding(
                    "DQ_TEMPORAL_002",
                    "temporal",
                    "warning",
                    "Temporal gaps detected",
                    "Observed intervals exceed the dominant interval.",
                    "Review missing periods before time-series preparation.",
                    column=name,
                    count=len(gaps),
                    evidence={
                        "expected_frequency": frequency,
                        "largest_gap_seconds": max(gaps),
                        "dominant_interval_seconds": dominant,
                    },
                    threshold={"gap_multiplier": settings.data_quality_temporal_gap_warning_multiplier},
                    confidence=0.85,
                )
            )
        irregular_ratio = len({round(value) for value in intervals}) / len(intervals)
        if irregular_ratio > 0.5 and len(intervals) >= 4:
            findings.append(
                _finding(
                    "DQ_TEMPORAL_005",
                    "temporal",
                    "warning",
                    "Irregular temporal frequency",
                    "Observed intervals have multiple inconsistent lengths.",
                    "Choose and document aggregation frequency in Phase 2D.",
                    column=name,
                    evidence={"interval_variation_ratio": irregular_ratio},
                    confidence=0.8,
                )
            )
    duplicate_dates = len(dates) - len(unique_dates)
    if duplicate_dates:
        findings.append(
            _finding(
                "DQ_TEMPORAL_006",
                "temporal",
                "info",
                "Duplicate timestamps",
                "Multiple rows share the same primary date; this may reflect dimensions.",
                "Confirm the intended dataset grain.",
                column=name,
                count=duplicate_dates,
                confidence=0.7,
            )
        )
    return {
        "available": True,
        "column": name,
        "frequency": frequency,
        "date_min": min(dates).isoformat() if dates else None,
        "date_max": max(dates).isoformat() if dates else None,
        "gap_count": len(gaps),
        "duplicate_dates": duplicate_dates,
        "out_of_order": len(out_of_order),
        "future_dates": len(future),
    }


def row_value(scan: QualityScan, row_index: int, column: str) -> str:
    return scan.rows[row_index - 2].get(column, "")


def _relationships(
    scan: QualityScan, roles: dict[str, str], settings: Settings, findings: list[dict[str, Any]]
) -> None:
    inequalities = (("clicks", "impressions"), ("conversions", "clicks"), ("orders", "conversions"))
    for lower, upper in inequalities:
        if lower in roles and upper in roles:
            bad = [
                i + 2
                for i, row in enumerate(scan.rows)
                if (a := parse_number(row.get(roles[lower], ""))) is not None
                and (b := parse_number(row.get(roles[upper], ""))) is not None
                and a > b
            ]
            if bad:
                findings.append(
                    _finding(
                        "DQ_RELATIONSHIP_001",
                        "metric_relationship",
                        "error",
                        f"{lower.title()} exceed {upper}",
                        "Observed values are inconsistent with the expected funnel relationship.",
                        "Verify definitions and aggregation grain.",
                        columns=[roles[lower], roles[upper]],
                        count=len(bad),
                        ratio=len(bad) / max(scan.scanned_rows, 1),
                        rows=bad[: settings.data_quality_evidence_rows],
                        confidence=0.9,
                    )
                )
    formulas = {
        "roas": ("revenue", "spend"),
        "ctr": ("clicks", "impressions"),
        "cpc": ("spend", "clicks"),
        "cpa": ("spend", "conversions"),
        "conversion_rate": ("conversions", "clicks"),
    }
    for result, (numerator, denominator) in formulas.items():
        if not all(role in roles for role in (result, numerator, denominator)):
            continue
        formula_bad: list[int] = []
        for i, row in enumerate(scan.rows, start=2):
            actual, num, den = (parse_number(row.get(roles[role], "")) for role in (result, numerator, denominator))
            if actual is None or num is None or den is None or den == 0:
                continue
            expected = num / den
            options = [expected, expected * 100] if result in {"ctr", "conversion_rate"} else [expected]
            if (
                min(abs(actual - option) / max(abs(option), 1e-9) for option in options)
                > settings.data_quality_relationship_tolerance
            ):
                formula_bad.append(i)
        if formula_bad:
            findings.append(
                _finding(
                    "DQ_RELATIONSHIP_002",
                    "metric_relationship",
                    "warning",
                    f"{result.upper()} relationship differs",
                    "Observed values differ from the approximate mapped-metric relationship; "
                    "aggregation definitions may explain this.",
                    "Review metric definitions and grain.",
                    columns=[roles[result], roles[numerator], roles[denominator]],
                    count=len(formula_bad),
                    ratio=len(formula_bad) / max(scan.scanned_rows, 1),
                    rows=formula_bad[: settings.data_quality_evidence_rows],
                    threshold={"relative_tolerance": settings.data_quality_relationship_tolerance},
                    confidence=0.8,
                )
            )


def _leakage(
    scan: QualityScan,
    roles: dict[str, str],
    columns: dict[str, DatasetColumnProfile],
    settings: Settings,
    findings: list[dict[str, Any]],
) -> None:
    target_role = next((role for role in TARGET_ROLES if role in roles), None)
    target = roles.get(target_role) if target_role else None
    patterns = ("next_", "future_", "after_", "final_", "actual_", "realized_", "post_")
    for name, profile in columns.items():
        normalized = profile.normalized_column_name
        if any(token in normalized for token in patterns):
            findings.append(
                _finding(
                    "DQ_LEAKAGE_002",
                    "leakage",
                    "warning",
                    "Possible future or post-outcome signal",
                    "The column name heuristically suggests information unavailable at prediction time.",
                    "Document availability timing before using this column.",
                    column=name,
                    confidence=0.7,
                )
            )
    if not target:
        return
    target_values = [row.get(target, "") for row in scan.rows]
    for name, profile in columns.items():
        if name == target or profile.semantic_role in {"ignored", "date", "timestamp"}:
            continue
        compared = [
            (a, b) for a, b in zip(target_values, [row.get(name, "") for row in scan.rows], strict=True) if a and b
        ]
        if len(compared) >= 3 and all(a == b for a, b in compared):
            findings.append(
                _finding(
                    "DQ_LEAKAGE_001",
                    "leakage",
                    "blocker",
                    "Direct target copy detected",
                    "A non-target column exactly copies the target across comparable scanned rows.",
                    "Exclude the copy from future predictors and review lineage.",
                    column=name,
                    columns=[target],
                    count=len(compared),
                    ratio=1.0,
                    blocking=True,
                    confidence=1.0,
                )
            )
    for derived in ("roas", "profit"):
        if derived in roles and target_role == "revenue":
            findings.append(
                _finding(
                    "DQ_LEAKAGE_003",
                    "leakage",
                    "warning",
                    "Target-derived metric risk",
                    f"Mapped {derived} may mathematically incorporate revenue.",
                    "Establish prediction-time availability before use.",
                    column=roles[derived],
                    columns=[target],
                    confidence=0.85,
                )
            )


def analyze_quality(db: Session, dataset_id: str, settings: Settings, notes: str | None = None) -> QualityReportDetail:
    started = monotonic()
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise DatasetNotReadyForQualityAnalysisError("Dataset was not found")
    if dataset.status != DatasetStatus.ready:
        raise DatasetNotReadyForQualityAnalysisError("Dataset must be active and ready")
    schema = _active_schema(db, dataset_id)
    path = _raw_path(dataset, settings)
    version = (
        db.scalar(
            select(func.max(DatasetQualityReport.report_version)).where(DatasetQualityReport.dataset_id == dataset_id)
        )
        or 0
    ) + 1
    scan = scan_csv(path, dataset.encoding or "utf-8", dataset.delimiter or ",", settings)
    findings, summary = evaluate(scan, schema, settings)
    dimensions, overall, readiness = score(findings, settings.data_quality_score_blocker_cap)
    config = {key: value for key, value in settings.model_dump().items() if key.startswith("data_quality_")}
    report = DatasetQualityReport(
        id=None,
        dataset_id=dataset_id,
        schema_profile_id=schema.id,
        report_version=version,
        quality_engine_version=settings.data_quality_engine_version,
        status=QualityReportStatus.running,
        readiness_status=readiness,
        overall_score=overall,
        completeness_score=dimensions["completeness"],
        uniqueness_score=dimensions["uniqueness"],
        validity_score=dimensions["validity"],
        consistency_score=dimensions["consistency"],
        temporal_score=dimensions["temporal"],
        integrity_score=dimensions["integrity"],
        leakage_safety_score=dimensions["leakage_safety"],
        scanned_rows=scan.scanned_rows,
        total_rows=dataset.row_count,
        scan_coverage_ratio=round(scan.scanned_rows / max(dataset.row_count, 1), 6),
        analyzed_columns=len([c for c in schema.columns if c.semantic_role != "ignored"]),
        dataset_checksum=dataset.checksum_sha256,
        schema_version=schema.schema_version,
        configuration_hash=hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest(),
        summary_json=summary,
        recommendations_json=[
            {"message": item["recommendation"], "rule_code": item["rule_code"]} for item in findings[:20]
        ],
        metadata_json={"notes": notes, "scanned": "bounded" if scan.scanned_rows < dataset.row_count else "full"},
    )
    db.add(report)
    db.flush()
    for item in findings:
        db.add(
            DatasetQualityFinding(
                quality_report_id=report.id,
                dataset_id=dataset_id,
                rule_code=item["rule_code"],
                category=item["category"],
                severity=QualitySeverity(item["severity"]),
                title=item["title"],
                description=item["description"],
                affected_column=item["affected_column"],
                related_columns_json=item["related_columns"],
                affected_row_count=item["affected_row_count"],
                affected_ratio=item["affected_ratio"],
                sample_row_indices_json=item["sample_row_indices"],
                evidence_json=item["evidence"],
                threshold_json=item["threshold"],
                recommendation=item["recommendation"],
                blocking=item["blocking"],
                confidence=item["confidence"],
            )
        )
    counts = {
        severity: sum(item["severity"] == severity for item in findings)
        for severity in ("blocker", "error", "warning", "info")
    }
    now = datetime.now(UTC)
    report.total_findings = len(findings)
    report.blocker_count = counts["blocker"]
    report.error_count = counts["error"]
    report.warning_count = counts["warning"]
    report.info_count = counts["info"]
    report.duration_ms = round((monotonic() - started) * 1000)
    report.completed_at = now
    report.status = QualityReportStatus.completed
    db.execute(
        update(DatasetQualityReport)
        .where(
            DatasetQualityReport.dataset_id == dataset_id,
            DatasetQualityReport.id != report.id,
            DatasetQualityReport.status == QualityReportStatus.completed,
        )
        .values(status=QualityReportStatus.superseded, superseded_at=now)
    )
    db.commit()
    logger.info(
        "quality_analysis_completed dataset_id=%s schema_version=%s report_version=%s "
        "scanned_rows=%s findings=%s duration_ms=%s",
        dataset_id,
        schema.schema_version,
        version,
        scan.scanned_rows,
        len(findings),
        report.duration_ms,
    )
    return quality_detail(db, dataset_id)


def _finding_response(item: DatasetQualityFinding) -> QualityFindingResponse:
    return QualityFindingResponse(
        id=item.id,
        rule_code=item.rule_code,
        category=item.category,
        severity=item.severity.value,
        title=item.title,
        description=item.description,
        affected_column=item.affected_column,
        related_columns=item.related_columns_json,
        affected_row_count=item.affected_row_count,
        affected_ratio=item.affected_ratio,
        sample_row_indices=item.sample_row_indices_json,
        evidence=item.evidence_json,
        threshold=item.threshold_json,
        recommendation=item.recommendation,
        blocking=item.blocking,
        confidence=item.confidence,
    )


def quality_detail(db: Session, dataset_id: str) -> QualityReportDetail:
    report = db.scalar(
        select(DatasetQualityReport)
        .options(selectinload(DatasetQualityReport.findings))
        .where(
            DatasetQualityReport.dataset_id == dataset_id, DatasetQualityReport.status == QualityReportStatus.completed
        )
        .order_by(DatasetQualityReport.report_version.desc())
    )
    if report is None:
        raise QualityReportNotFoundError("Quality report was not found")
    dataset = db.get(Dataset, dataset_id)
    return QualityReportDetail(
        id=report.id,
        dataset_id=dataset_id,
        dataset_filename=dataset.original_filename if dataset else "Unknown",
        report_version=report.report_version,
        schema_version=report.schema_version,
        quality_engine_version=report.quality_engine_version,
        status=report.status.value,
        readiness_status=report.readiness_status.value,
        overall_score=report.overall_score,
        dimension_scores=QualityDimensionScores(
            completeness=report.completeness_score,
            uniqueness=report.uniqueness_score,
            validity=report.validity_score,
            consistency=report.consistency_score,
            temporal=report.temporal_score,
            integrity=report.integrity_score,
            leakage_safety=report.leakage_safety_score,
        ),
        total_findings=report.total_findings,
        blocker_count=report.blocker_count,
        error_count=report.error_count,
        warning_count=report.warning_count,
        info_count=report.info_count,
        scanned_rows=report.scanned_rows,
        total_rows=report.total_rows,
        scan_coverage_ratio=report.scan_coverage_ratio,
        analyzed_columns=report.analyzed_columns,
        created_at=report.created_at,
        completed_at=report.completed_at,
        duration_ms=report.duration_ms,
        summary=report.summary_json,
        recommendations=report.recommendations_json,
        findings=[_finding_response(item) for item in report.findings],
    )


def quality_history(db: Session, dataset_id: str) -> QualityHistoryResponse:
    reports = db.scalars(
        select(DatasetQualityReport)
        .where(DatasetQualityReport.dataset_id == dataset_id)
        .order_by(DatasetQualityReport.report_version.desc())
    ).all()
    return QualityHistoryResponse(
        items=[
            QualityHistoryItem(
                id=r.id,
                report_version=r.report_version,
                schema_version=r.schema_version,
                status=r.status.value,
                readiness_status=r.readiness_status.value,
                overall_score=r.overall_score,
                blocker_count=r.blocker_count,
                created_at=r.created_at,
            )
            for r in reports
        ]
    )


def quality_findings(
    db: Session,
    dataset_id: str,
    page: int,
    page_size: int,
    category: str | None,
    severity: str | None,
    blocking: bool | None,
    column: str | None,
) -> QualityFindingListResponse:
    report = db.scalar(
        select(DatasetQualityReport)
        .where(
            DatasetQualityReport.dataset_id == dataset_id, DatasetQualityReport.status == QualityReportStatus.completed
        )
        .order_by(DatasetQualityReport.report_version.desc())
    )
    if report is None:
        raise QualityReportNotFoundError("Quality report was not found")
    filters = [DatasetQualityFinding.quality_report_id == report.id]
    if category:
        filters.append(DatasetQualityFinding.category == category)
    if severity:
        filters.append(DatasetQualityFinding.severity == QualitySeverity(severity))
    if blocking is not None:
        filters.append(DatasetQualityFinding.blocking == blocking)
    if column:
        filters.append(DatasetQualityFinding.affected_column == column)
    total = db.scalar(select(func.count()).select_from(DatasetQualityFinding).where(*filters)) or 0
    items = db.scalars(
        select(DatasetQualityFinding)
        .where(*filters)
        .order_by(DatasetQualityFinding.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return QualityFindingListResponse(
        items=[_finding_response(item) for item in items],
        pagination=PaginationMetadata(
            page=page, page_size=page_size, total_items=total, total_pages=(total + page_size - 1) // page_size
        ),
    )


def quality_stats(db: Session) -> QualityStatsResponse:
    active_ids = select(Dataset.id).where(Dataset.status == DatasetStatus.ready)
    active_count = (
        db.scalar(select(func.count()).select_from(Dataset).where(Dataset.status == DatasetStatus.ready)) or 0
    )
    reports = db.scalars(
        select(DatasetQualityReport).where(
            DatasetQualityReport.dataset_id.in_(active_ids),
            DatasetQualityReport.status == QualityReportStatus.completed,
        )
    ).all()
    return QualityStatsResponse(
        datasets_not_analyzed=max(active_count - len(reports), 0),
        blocked_datasets=sum(r.readiness_status == QualityReadiness.blocked for r in reports),
        needs_attention=sum(r.readiness_status == QualityReadiness.needs_attention for r in reports),
        conditionally_ready=sum(r.readiness_status == QualityReadiness.conditionally_ready for r in reports),
        quality_ready=sum(r.readiness_status == QualityReadiness.quality_ready for r in reports),
        total_blockers=sum(r.blocker_count for r in reports),
        average_quality_score=round(sum(r.overall_score for r in reports) / len(reports), 2) if reports else None,
    )
