import csv
import hashlib
import json
import math
import statistics
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.models.dataset import Dataset, DatasetStatus
from app.models.preparation import (
    PreparationEvent,
    PreparationReadiness,
    PreparationStatus,
    PreparedDataset,
    PreparedFeature,
)
from app.models.quality import DatasetQualityReport, QualityReadiness, QualityReportStatus
from app.models.schema_profile import DatasetColumnProfile, DatasetSchemaProfile, SchemaStatus
from app.schemas.preparation import (
    BacktestFoldDefinition,
    FeatureCatalogResponse,
    PreparationConfig,
    PreparationHistoryResponse,
    PreparationPreviewResponse,
    PreparationResponse,
    PreparationSplitResponse,
    PreparationStatsResponse,
    PreparationSummary,
    PreparationWarning,
    PreparedFeatureResponse,
    SplitDefinition,
)
from app.services.preparation_storage_service import PreparationStorageService

FLOW_ROLES = {
    "revenue",
    "spend",
    "impressions",
    "clicks",
    "conversions",
    "orders",
    "units_sold",
    "cost",
    "profit",
    "sessions",
    "users",
}
RATIO_SOURCES = {
    "ctr": ("clicks", "impressions"),
    "conversion_rate": ("conversions", "clicks"),
    "roas": ("revenue", "spend"),
    "cpc": ("spend", "clicks"),
    "cpa": ("spend", "conversions"),
    "average_order_value": ("revenue", "orders"),
}


class PreparationError(ValueError):
    pass


def _number(value: str | None) -> float | None:
    try:
        result = float((value or "").strip())
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def _date(value: str) -> datetime:
    clean = value.strip().replace("Z", "+00:00")
    for parser in (
        datetime.fromisoformat,
        lambda x: datetime.strptime(x, "%d/%m/%Y"),
        lambda x: datetime.strptime(x, "%m/%d/%Y"),
    ):
        try:
            parsed = parser(clean)
            return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
        except ValueError:
            continue
    raise PreparationError("Critical date values could not be parsed")


def _bucket(value: datetime, frequency: str) -> datetime:
    if frequency == "hourly":
        return value.replace(minute=0, second=0, microsecond=0)
    if frequency == "daily":
        return value.replace(hour=0, minute=0, second=0, microsecond=0)
    if frequency == "weekly":
        return (value - timedelta(days=value.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    if frequency == "monthly":
        return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    quarter_month = ((value.month - 1) // 3) * 3 + 1
    return value.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)


def _next_period(value: datetime, frequency: str) -> datetime:
    if frequency == "hourly":
        return value + timedelta(hours=1)
    if frequency == "daily":
        return value + timedelta(days=1)
    if frequency == "weekly":
        return value + timedelta(days=7)
    months = 1 if frequency == "monthly" else 3
    month = value.month - 1 + months
    return value.replace(year=value.year + month // 12, month=month % 12 + 1)


def _source_path(dataset: Dataset, settings: Settings) -> Path:
    root = settings.dataset_storage_root.resolve()
    path = (root / dataset.storage_key).resolve()
    if root not in path.parents or not path.is_file():
        raise PreparationError("Immutable source file is unavailable")
    return path


def _sources(schema: DatasetSchemaProfile) -> tuple[dict[str, DatasetColumnProfile], dict[str, str]]:
    by_name = {c.column_name: c for c in schema.columns}
    by_role: dict[str, str] = {}
    for column in schema.columns:
        if column.semantic_role not in {"ignored", "unknown"} and column.semantic_role not in by_role:
            by_role[column.semantic_role] = column.column_name
    return by_name, by_role


def _validate_source(
    db: Session, dataset_id: str, config: PreparationConfig, settings: Settings
) -> tuple[Dataset, DatasetSchemaProfile, DatasetQualityReport]:
    dataset = db.get(Dataset, dataset_id)
    if not dataset or dataset.status != DatasetStatus.ready:
        raise PreparationError("Dataset must be active and ready")
    schema = db.scalar(
        select(DatasetSchemaProfile)
        .options(selectinload(DatasetSchemaProfile.columns))
        .where(DatasetSchemaProfile.dataset_id == dataset_id, DatasetSchemaProfile.status == SchemaStatus.confirmed)
        .order_by(DatasetSchemaProfile.schema_version.desc())
    )
    if not schema:
        raise PreparationError("A confirmed schema mapping is required")
    quality = db.scalar(
        select(DatasetQualityReport)
        .where(
            DatasetQualityReport.dataset_id == dataset_id, DatasetQualityReport.status == QualityReportStatus.completed
        )
        .order_by(DatasetQualityReport.report_version.desc())
    )
    if not quality:
        raise PreparationError("A completed data-quality report is required")
    if quality.schema_profile_id != schema.id or quality.dataset_checksum != dataset.checksum_sha256:
        raise PreparationError("Quality report is stale for the confirmed schema")
    if quality.readiness_status == QualityReadiness.blocked:
        raise PreparationError("Blocking quality findings must be resolved before preparation")
    if quality.readiness_status in {
        QualityReadiness.needs_attention,
        QualityReadiness.conditionally_ready,
    } and not (
        settings.preparation_allow_quality_override and config.quality_override and config.quality_override_reason
    ):
        raise PreparationError("Conditional quality readiness requires an enabled override and reason")
    columns = {c.column_name: c for c in schema.columns}
    if config.date_column not in columns or columns[config.date_column].semantic_role not in {"date", "timestamp"}:
        raise PreparationError("Date column must use a confirmed date or timestamp mapping")
    if config.target_column not in columns or columns[config.target_column].physical_type.value not in {
        "integer",
        "float",
    }:
        raise PreparationError("Target column must use a confirmed numeric mapping")
    if len(config.group_columns) > settings.preparation_max_groups or any(
        x not in columns for x in config.group_columns
    ):
        raise PreparationError("Grouping configuration is invalid")
    if (
        max(config.lag_periods or [0]) > settings.preparation_max_lag
        or max(config.rolling_windows or [0]) > settings.preparation_max_rolling_window
    ):
        raise PreparationError("Lag or rolling window exceeds configured limits")
    _source_path(dataset, settings)
    return dataset, schema, quality


def _aggregate(
    rows: list[dict[str, str]], config: PreparationConfig, schema: DatasetSchemaProfile
) -> tuple[list[dict[str, Any]], int]:
    columns, roles = _sources(schema)
    buckets: dict[tuple[object, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        moment = _bucket(_date(row.get(config.date_column, "")), config.frequency)
        key: tuple[object, ...] = (*[row.get(x, "") for x in config.group_columns], moment)
        buckets[key].append(row)
    duplicates = sum(max(len(items) - 1, 0) for items in buckets.values())
    if duplicates and config.duplicate_period_policy == "reject":
        raise PreparationError("Duplicate date/group periods require aggregation")
    output: list[dict[str, Any]] = []
    for key, items in sorted(buckets.items(), key=lambda x: tuple(str(v) for v in x[0])):
        result: dict[str, Any] = {name: key[i] for i, name in enumerate(config.group_columns)}
        period = cast(datetime, key[-1])
        result[config.date_column] = period.date().isoformat() if config.frequency != "hourly" else period.isoformat()
        for name, profile in columns.items():
            if name in result or profile.semantic_role in {"ignored", "date", "timestamp"}:
                continue
            values = [_number(row.get(name)) for row in items]
            numeric = [x for x in values if x is not None]
            rule = config.aggregation_rules.get(name, "sum" if profile.semantic_role in FLOW_ROLES else "mean")
            if numeric:
                result[name] = (
                    sum(numeric)
                    if rule == "sum"
                    else (
                        min(numeric)
                        if rule == "min"
                        else max(numeric)
                        if rule == "max"
                        else (numeric[-1] if rule == "last" else statistics.fmean(numeric))
                    )
                )
            else:
                nonempty = [row.get(name, "") for row in items if row.get(name, "").strip()]
                result[name] = nonempty[-1] if nonempty else None
        for role, (numerator_role, denominator_role) in RATIO_SOURCES.items():
            existing, numerator, denominator = roles.get(role), roles.get(numerator_role), roles.get(denominator_role)
            if existing and numerator and denominator and numerator in result and denominator in result:
                den = _number(str(result[denominator]))
                num = _number(str(result[numerator]))
                result[existing] = num / den if num is not None and den is not None and den != 0 else None
        output.append(result)
    return output, duplicates


def _align(
    rows: list[dict[str, Any]], config: PreparationConfig, schema: DatasetSchemaProfile
) -> tuple[list[dict[str, Any]], int]:
    if config.missing_period_policy == "preserve":
        return rows, 0
    _, roles = _sources(schema)
    flow_columns = {name for role, name in roles.items() if role in FLOW_ROLES}
    grouped: dict[tuple[object, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(x) for x in config.group_columns)].append(row)
    result: list[dict[str, Any]] = []
    generated = 0
    for group, items in grouped.items():
        indexed = {_date(str(row[config.date_column])): row for row in items}
        current, end = min(indexed), max(indexed)
        while current <= end:
            if current in indexed:
                result.append(indexed[current])
            else:
                if config.missing_period_policy == "reject":
                    raise PreparationError("Missing time periods are present")
                row = {name: value for name, value in zip(config.group_columns, group, strict=True)}
                row[config.date_column] = current.date().isoformat()
                row["is_generated_period"] = 1
                if config.missing_period_policy == "insert_zero_for_flow_metrics":
                    row.update({x: 0 for x in flow_columns if x != config.target_column})
                result.append(row)
                generated += 1
            current = _next_period(current, config.frequency)
    return sorted(
        result, key=lambda r: (*[str(r.get(x, "")) for x in config.group_columns], str(r[config.date_column]))
    ), generated


def _features(
    rows: list[dict[str, Any]], config: PreparationConfig, schema: DatasetSchemaProfile
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    columns, roles = _sources(schema)
    catalog: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for name, profile in columns.items():
        included = profile.semantic_role != "ignored"
        catalog.append(
            {
                "feature_name": name,
                "source_columns": [name],
                "feature_type": "target"
                if name == config.target_column
                else (
                    "date"
                    if name == config.date_column
                    else "dimension"
                    if profile.physical_type.value in {"categorical", "identifier", "text"}
                    else "raw_numeric"
                ),
                "transformation_type": "aggregation",
                "semantic_role": profile.semantic_role,
                "physical_type": profile.physical_type.value,
                "availability_type": "target_derived" if name == config.target_column else "unknown",
                "leakage_risk": "excluded_target" if name == config.target_column else "review",
                "included": included,
                "generated": False,
                "parameters": {},
                "lineage": {"source_dataset_column": name},
                "description": "Aggregated immutable source column.",
            }
        )
    grouped: dict[tuple[object, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(x) for x in config.group_columns)].append(row)
    for items in grouped.values():
        items.sort(key=lambda x: str(x[config.date_column]))
        history: list[float | None] = []
        start = _date(str(items[0][config.date_column]))
        for index, row in enumerate(items):
            current = _number(str(row.get(config.target_column, "")))
            for lag in config.lag_periods:
                row[f"{config.target_column}_lag_{lag}"] = history[index - lag] if index >= lag else None
            for window in config.rolling_windows:
                prior = [x for x in history[max(0, index - window) : index] if x is not None]
                for stat in config.rolling_statistics:
                    value = None
                    if prior:
                        value = (
                            sum(prior)
                            if stat == "sum"
                            else (
                                min(prior)
                                if stat == "min"
                                else max(prior)
                                if stat == "max"
                                else statistics.fmean(prior)
                            )
                        )
                    row[f"{config.target_column}_rolling_{stat}_{window}"] = value
            moment = _date(str(row[config.date_column]))
            if config.include_calendar_features:
                row.update(
                    {
                        "calendar_year": moment.year,
                        "calendar_quarter": ((moment.month - 1) // 3) + 1,
                        "calendar_month": moment.month,
                        "calendar_week": moment.isocalendar().week,
                        "calendar_day_of_week": moment.weekday(),
                        "calendar_is_weekend": int(moment.weekday() >= 5),
                        "calendar_month_sin": math.sin(2 * math.pi * moment.month / 12),
                        "calendar_month_cos": math.cos(2 * math.pi * moment.month / 12),
                    }
                )
            if config.include_trend_features:
                row["periods_since_start"] = index
                row["days_since_start"] = (moment - start).days
            if config.include_holiday_features:
                row["is_holiday"] = int(moment.date().isoformat() in config.holiday_dates)
            history.append(current)
    for lag in config.lag_periods:
        catalog.append(
            _generated(
                f"{config.target_column}_lag_{lag}", [config.target_column], "lag", "historical_only", {"periods": lag}
            )
        )
    for window in config.rolling_windows:
        for stat in config.rolling_statistics:
            catalog.append(
                _generated(
                    f"{config.target_column}_rolling_{stat}_{window}",
                    [config.target_column],
                    "rolling",
                    "historical_only",
                    {"window": window, "shift": 1, "statistic": stat},
                )
            )
    if config.include_calendar_features:
        for name in (
            "calendar_year",
            "calendar_quarter",
            "calendar_month",
            "calendar_week",
            "calendar_day_of_week",
            "calendar_is_weekend",
            "calendar_month_sin",
            "calendar_month_cos",
        ):
            catalog.append(_generated(name, [config.date_column], "calendar", "known_in_advance", {}))
    if config.include_trend_features:
        for name in ("periods_since_start", "days_since_start"):
            catalog.append(_generated(name, [config.date_column], "trend", "known_in_advance", {}))
    if config.include_holiday_features:
        catalog.append(
            _generated("is_holiday", [config.date_column], "holiday", "known_in_advance", {"calendar": "user_provided"})
        )
    if config.include_derived_metrics:
        for role, (num_role, den_role) in RATIO_SOURCES.items():
            if role in roles or num_role not in roles or den_role not in roles:
                continue
            unsafe = roles[num_role] == config.target_column
            catalog.append(
                _generated(
                    role,
                    [roles[num_role], roles[den_role]],
                    "derived_metric",
                    "target_derived" if unsafe else "observed_at_prediction_time",
                    {"safe_division": True},
                    included=not unsafe,
                    risk="target_derived" if unsafe else "none",
                )
            )
            if unsafe:
                warnings.append(
                    {
                        "code": "TARGET_DERIVED_EXCLUDED",
                        "message": f"{role} was excluded because it uses the same-period target.",
                    }
                )
            else:
                for row in rows:
                    num, den = _number(str(row.get(roles[num_role], ""))), _number(str(row.get(roles[den_role], "")))
                    row[role] = num / den if num is not None and den is not None and den != 0 else None
    return rows, catalog, warnings


def _generated(
    name: str,
    sources: list[str],
    kind: str,
    availability: str,
    params: dict[str, object],
    included: bool = True,
    risk: str = "none",
) -> dict[str, Any]:
    return {
        "feature_name": name,
        "source_columns": sources,
        "feature_type": kind,
        "transformation_type": kind,
        "semantic_role": "unknown",
        "physical_type": "float",
        "availability_type": availability,
        "leakage_risk": risk,
        "included": included,
        "generated": True,
        "parameters": params,
        "lineage": {"source_columns": sources, "historical_only": availability == "historical_only"},
        "description": f"Deterministic {kind} feature.",
    }


def _split(
    rows: list[dict[str, Any]], config: PreparationConfig, settings: Settings
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    dates = sorted({_date(str(row[config.date_column])).date().isoformat() for row in rows})
    if len(dates) < settings.preparation_min_periods:
        raise PreparationError("Insufficient temporal history for governed splitting")
    if config.train_end_date and config.validation_end_date:
        final_end = config.test_end_date or dates[-1]
        train_dates = [value for value in dates if value <= config.train_end_date]
        validation_dates = [value for value in dates if config.train_end_date < value <= config.validation_end_date]
        test_dates = [value for value in dates if config.validation_end_date < value <= final_end]
    else:
        train_cut = max(1, int(len(dates) * config.train_ratio))
        validation_cut = train_cut + max(1, int(len(dates) * config.validation_ratio))
        if validation_cut >= len(dates):
            validation_cut = len(dates) - 1
        train_dates, validation_dates, test_dates = (
            dates[:train_cut],
            dates[train_cut:validation_cut],
            dates[validation_cut:],
        )
    if min(len(train_dates), len(validation_dates), len(test_dates)) < 1:
        raise PreparationError("Chronological split is too small")
    lookup = (
        {d: "train" for d in train_dates}
        | {d: "validation" for d in validation_dates}
        | {d: "test" for d in test_dates}
    )
    for row in rows:
        row["__split"] = lookup[_date(str(row[config.date_column])).date().isoformat()]
    splits = [
        {"name": name, "start": values[0], "end": values[-1], "rows": sum(row["__split"] == name for row in rows)}
        for name, values in (("train", train_dates), ("validation", validation_dates), ("test", test_dates))
    ]
    minimums = {
        "train": settings.preparation_min_train_rows,
        "validation": settings.preparation_min_validation_rows,
        "test": settings.preparation_min_test_rows,
    }
    if any(item["rows"] < minimums[item["name"]] for item in splits):
        raise PreparationError("Chronological split does not meet configured minimum row counts")
    folds: list[dict[str, Any]] = []
    validation_size = max(1, len(validation_dates))
    available = dates[: -len(test_dates)]
    for fold in range(config.backtest_folds):
        end = len(available) - (config.backtest_folds - fold) * validation_size
        if end < 2 or end + validation_size > len(available):
            continue
        folds.append(
            {
                "fold": fold + 1,
                "train_start": available[0],
                "train_end": available[end - 1],
                "validation_start": available[end],
                "validation_end": available[end + validation_size - 1],
            }
        )
    return rows, splits, folds


def create_preparation(
    db: Session, dataset_id: str, config: PreparationConfig, settings: Settings
) -> PreparationResponse:
    started = time.perf_counter()
    dataset, schema, quality = _validate_source(db, dataset_id, config, settings)
    version = (
        db.scalar(
            select(func.max(PreparedDataset.preparation_version)).where(PreparedDataset.source_dataset_id == dataset_id)
        )
        or 0
    ) + 1
    config_data = config.model_dump(mode="json")
    config_hash = hashlib.sha256(json.dumps(config_data, sort_keys=True).encode()).hexdigest()
    prepared = PreparedDataset(
        id=str(uuid.uuid4()),
        source_dataset_id=dataset_id,
        source_schema_profile_id=schema.id,
        source_quality_report_id=quality.id,
        preparation_version=version,
        preparation_engine_version=settings.preparation_engine_version,
        status=PreparationStatus.running,
        readiness_status=PreparationReadiness.preparing,
        configuration_json=config_data,
        configuration_hash=config_hash,
        source_checksum=dataset.checksum_sha256,
        target_column=config.target_column,
        date_column=config.date_column,
        group_columns_json=config.group_columns,
        frequency=config.frequency,
        forecast_horizon=config.forecast_horizon,
    )
    db.add(prepared)
    db.commit()
    storage = PreparationStorageService(settings)
    try:
        with _source_path(dataset, settings).open(encoding=dataset.encoding or "utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=dataset.delimiter or ","))
        if len(rows) > settings.preparation_max_rows:
            raise PreparationError("Dataset exceeds preparation row limit")
        raw_hash = hashlib.sha256(_source_path(dataset, settings).read_bytes()).hexdigest()
        if raw_hash != dataset.checksum_sha256:
            raise PreparationError("Source checksum changed; raw data integrity failed")
        aggregated, collapsed = _aggregate(rows, config, schema)
        group_count = len({tuple(row.get(name) for name in config.group_columns) for row in aggregated})
        if group_count > settings.preparation_max_groups:
            raise PreparationError("Prepared series count exceeds the configured group limit")
        aligned, generated = _align(aggregated, config, schema)
        transformed, catalog, warnings = _features(aligned, config, schema)
        transformed, splits, folds = _split(transformed, config, settings)
        before = len(transformed)
        if config.missing_target_policy == "drop_rows_missing_target":
            transformed = [r for r in transformed if _number(str(r.get(config.target_column, ""))) is not None]
        dropped = before - len(transformed)
        columns = list(dict.fromkeys(key for row in transformed for key in row))
        preview = [
            {key: None if row.get(key) is None else str(row.get(key))[:500] for key in columns}
            for row in transformed[: settings.preparation_preview_rows]
        ]
        manifest = {
            "source_dataset_id": dataset.id,
            "source_checksum": dataset.checksum_sha256,
            "schema_version": schema.schema_version,
            "quality_report_version": quality.report_version,
            "preparation_version": version,
            "engine_version": settings.preparation_engine_version,
            "configuration": config_data,
            "row_count": len(transformed),
            "columns": columns,
            "splits": splits,
            "backtest_folds": folds,
        }
        storage_key, checksum = storage.write(
            prepared.id,
            columns,
            transformed,
            {
                "manifest": manifest,
                "feature_catalog": catalog,
                "splits": {"splits": splits, "backtest_folds": folds},
                "preview": {"columns": columns, "rows": preview},
                "preparation_report": {
                    "collapsed_duplicate_rows": collapsed,
                    "generated_rows": generated,
                    "dropped_rows": dropped,
                    "warnings": warnings,
                },
            },
        )
        prepared.features = [
            PreparedFeature(
                prepared_dataset_id=prepared.id,
                **{k: v for k, v in item.items() if k not in {"source_columns", "parameters", "lineage"}},
                source_columns_json=item["source_columns"],
                parameters_json=item["parameters"],
                lineage_json=item["lineage"],
            )
            for item in catalog
        ]
        split_map = {x["name"]: x for x in splits}
        prepared.storage_key = storage_key
        prepared.prepared_checksum = checksum
        prepared.row_count = len(transformed)
        prepared.column_count = len(columns)
        prepared.feature_count = sum(x["included"] for x in catalog)
        prepared.train_rows = split_map["train"]["rows"]
        prepared.validation_rows = split_map["validation"]["rows"]
        prepared.test_rows = split_map["test"]["rows"]
        for name in ("train", "validation", "test"):
            setattr(prepared, f"{name}_start", split_map[name]["start"])
            setattr(prepared, f"{name}_end", split_map[name]["end"])
        prepared.dropped_rows = dropped
        prepared.generated_rows = generated
        prepared.warnings_json = warnings
        prepared.metadata_json = {
            "schema_version": schema.schema_version,
            "quality_report_version": quality.report_version,
            "collapsed_duplicate_rows": collapsed,
            "splits": splits,
            "backtest_folds": folds,
            "group_count": group_count,
        }
        prepared.duration_ms = int((time.perf_counter() - started) * 1000)
        prepared.completed_at = datetime.now(UTC)
        prepared.status = PreparationStatus.completed
        prepared.readiness_status = (
            PreparationReadiness.review_required if warnings else PreparationReadiness.model_ready
        )
        db.execute(
            update(PreparedDataset)
            .where(
                PreparedDataset.source_dataset_id == dataset_id,
                PreparedDataset.id != prepared.id,
                PreparedDataset.status == PreparationStatus.completed,
            )
            .values(status=PreparationStatus.superseded, superseded_at=datetime.now(UTC))
        )
        db.add(
            PreparationEvent(
                prepared_dataset_id=prepared.id,
                event_type="artifact_saved",
                message="Versioned preparation artifact saved.",
                metadata_json={"rows": len(transformed), "features": prepared.feature_count},
            )
        )
        db.commit()
        db.refresh(prepared)
        return _response(prepared, schema.schema_version, quality.report_version)
    except Exception as exc:
        storage.cleanup(prepared.id)
        prepared.status = PreparationStatus.failed
        prepared.readiness_status = PreparationReadiness.blocked
        prepared.failed_at = datetime.now(UTC)
        prepared.failure_message = str(exc)[:500]
        db.commit()
        raise


def _response(
    item: PreparedDataset, schema_version: int | None = None, quality_version: int | None = None
) -> PreparationResponse:
    config = PreparationConfig.model_validate(item.configuration_json)
    return PreparationResponse(
        id=item.id,
        source_dataset_id=item.source_dataset_id,
        preparation_version=item.preparation_version,
        status=item.status.value,
        readiness_status=item.readiness_status.value,
        row_count=item.row_count,
        column_count=item.column_count,
        feature_count=item.feature_count,
        frequency=item.frequency,
        created_at=item.created_at,
        preparation_engine_version=item.preparation_engine_version,
        source_schema_version=schema_version or int(item.metadata_json.get("schema_version", 0)),
        source_quality_report_version=quality_version or int(item.metadata_json.get("quality_report_version", 0)),
        source_checksum=item.source_checksum,
        prepared_checksum=item.prepared_checksum,
        target_column=item.target_column,
        date_column=item.date_column,
        group_columns=item.group_columns_json,
        forecast_horizon=item.forecast_horizon,
        train_rows=item.train_rows,
        validation_rows=item.validation_rows,
        test_rows=item.test_rows,
        dropped_rows=item.dropped_rows,
        generated_rows=item.generated_rows,
        duration_ms=item.duration_ms,
        warnings=[PreparationWarning.model_validate(x) for x in item.warnings_json],
        configuration=config,
        completed_at=item.completed_at,
    )


def get_preparation(db: Session, prepared_id: str) -> PreparationResponse:
    item = db.get(PreparedDataset, prepared_id)
    if not item:
        raise PreparationError("Prepared dataset was not found")
    schema = db.get(DatasetSchemaProfile, item.source_schema_profile_id)
    quality = db.get(DatasetQualityReport, item.source_quality_report_id)
    return _response(item, schema.schema_version if schema else 0, quality.report_version if quality else 0)


def list_preparations(db: Session, dataset_id: str) -> PreparationHistoryResponse:
    items = db.scalars(
        select(PreparedDataset)
        .where(PreparedDataset.source_dataset_id == dataset_id)
        .order_by(PreparedDataset.preparation_version.desc())
    ).all()
    return PreparationHistoryResponse(
        items=[
            PreparationSummary(
                id=x.id,
                source_dataset_id=x.source_dataset_id,
                preparation_version=x.preparation_version,
                status=x.status.value,
                readiness_status=x.readiness_status.value,
                row_count=x.row_count,
                column_count=x.column_count,
                feature_count=x.feature_count,
                frequency=x.frequency,
                created_at=x.created_at,
            )
            for x in items
        ]
    )


def get_features(db: Session, prepared_id: str) -> FeatureCatalogResponse:
    item = db.scalar(
        select(PreparedDataset).options(selectinload(PreparedDataset.features)).where(PreparedDataset.id == prepared_id)
    )
    if not item:
        raise PreparationError("Prepared dataset was not found")
    return FeatureCatalogResponse(
        prepared_dataset_id=item.id,
        items=[
            PreparedFeatureResponse(
                id=x.id,
                feature_name=x.feature_name,
                source_columns=x.source_columns_json,
                feature_type=x.feature_type,
                transformation_type=x.transformation_type,
                semantic_role=x.semantic_role,
                physical_type=x.physical_type,
                availability_type=x.availability_type,
                leakage_risk=x.leakage_risk,
                included=x.included,
                generated=x.generated,
                parameters=x.parameters_json,
                lineage=x.lineage_json,
                description=x.description,
            )
            for x in item.features
        ],
    )


def get_preview(db: Session, prepared_id: str, settings: Settings) -> PreparationPreviewResponse:
    if not db.get(PreparedDataset, prepared_id):
        raise PreparationError("Prepared dataset was not found")
    payload = PreparationStorageService(settings).json_file(prepared_id, "preview")
    assert isinstance(payload, dict)
    return PreparationPreviewResponse(
        prepared_dataset_id=prepared_id,
        columns=payload["columns"],
        rows=payload["rows"],
        returned_rows=len(payload["rows"]),
    )


def get_splits(db: Session, prepared_id: str, settings: Settings) -> PreparationSplitResponse:
    if not db.get(PreparedDataset, prepared_id):
        raise PreparationError("Prepared dataset was not found")
    payload = PreparationStorageService(settings).json_file(prepared_id, "splits")
    assert isinstance(payload, dict)
    return PreparationSplitResponse(
        prepared_dataset_id=prepared_id,
        splits=[SplitDefinition.model_validate(x) for x in payload["splits"]],
        backtest_folds=[BacktestFoldDefinition.model_validate(x) for x in payload["backtest_folds"]],
    )


def get_stats(db: Session) -> PreparationStatsResponse:
    all_items = db.scalars(select(PreparedDataset)).all()
    completed = [x for x in all_items if x.status in {PreparationStatus.completed, PreparationStatus.superseded}]
    active_count = (
        db.scalar(select(func.count()).select_from(Dataset).where(Dataset.status == DatasetStatus.ready)) or 0
    )
    prepared_ids = {x.source_dataset_id for x in completed}
    return PreparationStatsResponse(
        total_prepared_datasets=len(completed),
        model_ready_datasets=sum(x.readiness_status == PreparationReadiness.model_ready for x in completed),
        failed_preparations=sum(x.status == PreparationStatus.failed for x in all_items),
        average_feature_count=statistics.fmean(x.feature_count for x in completed) if completed else None,
        average_duration_ms=statistics.fmean(x.duration_ms for x in completed) if completed else None,
        datasets_awaiting_preparation=max(active_count - len(prepared_ids), 0),
    )
