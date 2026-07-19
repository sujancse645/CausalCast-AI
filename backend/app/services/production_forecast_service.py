from __future__ import annotations

import csv
import hashlib
import json
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.config import Settings, get_settings
from app.schemas.production_forecast import (
    ProductionDatasetMetadata,
    ProductionDatasetSummary,
    ProductionForecastResponse,
    ProductionModelSummary,
    ProductionPrediction,
    ProductionReportResponse,
)


class ProductionAssetNotFoundError(LookupError):
    pass


class ProductionAssetInvalidError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ForecastAsset:
    id: str
    name: str
    model_name: str
    model_type: str
    model_relative: str
    data_relative: str
    report_relative: str
    target: str
    timestamp: str
    frequency: str
    default_horizon: int
    selected_metric: str
    series_dimension: str | None = None


ASSETS = {
    "rossmann": ForecastAsset(
        "rossmann",
        "Rossmann Store Sales",
        "rossmann_xgboost_v1",
        "XGBRegressor",
        "artifacts/models/rossmann_xgboost_v1/model.joblib",
        "datasets/raw/rossmann/train.csv",
        "artifacts/models/rossmann_xgboost_v1/metadata.json",
        "Sales",
        "Date",
        "daily",
        30,
        "rmse",
    ),
    "electricity": ForecastAsset(
        "electricity",
        "Electricity Load",
        "lightgbm_electricity",
        "LGBMRegressor",
        "models/electricity/lightgbm_electricity.pkl",
        "datasets/features/electricity/electricity_features.csv",
        "reports/electricity/model_comparison.csv",
        "total_load",
        "timestamp",
        "hourly",
        24,
        "RMSE",
    ),
    "m4_daily": ForecastAsset(
        "m4_daily",
        "M4 Daily",
        "lightgbm_m4",
        "LGBMRegressor",
        "models/m4_daily/lightgbm_m4.pkl",
        "datasets/training/m4_daily/m4_test.parquet",
        "reports/m4_daily/model_comparison.json",
        "value",
        "timestamp",
        "daily",
        14,
        "RMSE",
        "series_name",
    ),
    "online_retail": ForecastAsset(
        "online_retail",
        "Online Retail II",
        "xgboost_model",
        "XGBRegressor",
        "models/online_retail/xgboost_model.pkl",
        "datasets/training/online_retail/test.parquet",
        "reports/online_retail/model_comparison.json",
        "Revenue",
        "Date",
        "daily",
        14,
        "RMSE",
    ),
    "tourism": ForecastAsset(
        "tourism",
        "Tourism (yearly source)",
        "xgboost_model",
        "XGBRegressor",
        "models/tourism/xgboost_model.pkl",
        "datasets/training/tourism/test.parquet",
        "reports/tourism/model_comparison.json",
        "value",
        "timestamp",
        "yearly",
        8,
        "RMSE",
        "series_name",
    ),
}


class ProductionForecastService:
    """Read-only inference over allowlisted, already-trained project artifacts."""

    def __init__(self, settings: Settings) -> None:
        self.project_root = settings.project_root.resolve()
        self._model_cache: dict[str, Any] = {}
        self._model_lock = threading.RLock()

    def datasets(self) -> list[ProductionDatasetSummary]:
        return [self._summary(asset) for asset in ASSETS.values()]

    def models(self) -> list[ProductionModelSummary]:
        items: list[ProductionModelSummary] = []
        for asset in ASSETS.values():
            path = self._path(asset.model_relative)
            metrics = self._selected_metrics(asset)
            if not path.is_file() or asset.selected_metric not in metrics:
                continue
            items.append(
                ProductionModelSummary(
                    id=f"{asset.id}:{asset.model_name}",
                    dataset_id=asset.id,
                    name=asset.model_name,
                    model_type=asset.model_type,
                    selected_metric=asset.selected_metric.lower(),
                    selected_metric_value=metrics[asset.selected_metric],
                    checksum=self._checksum(path),
                    loaded=asset.id in self._model_cache,
                )
            )
        return items

    def metadata(self, dataset: str) -> ProductionDatasetMetadata:
        asset = self._asset(dataset)
        model_path = self._path(asset.model_relative)
        data_path = self._path(asset.data_relative)
        features = self._features(asset) if model_path.is_file() else []
        series = self._series_values(asset, data_path) if data_path.is_file() and asset.series_dimension else []
        return ProductionDatasetMetadata(
            **self._summary(asset).model_dump(),
            features=features,
            series_dimension=asset.series_dimension,
            series_count=len(series) if asset.series_dimension else None,
            example_series=series[:20],
            prediction_kind="held_out_test",
            metrics=self._selected_metrics(asset),
            model_checksum=self._checksum(model_path) if model_path.is_file() else None,
        )

    def forecast(
        self, dataset: str, horizon: int | None = None, series: str | None = None
    ) -> ProductionForecastResponse:
        started = time.perf_counter()
        asset = self._asset(dataset)
        requested_horizon = horizon or asset.default_horizon
        model, loaded_from_disk = self._model(asset)
        features = self._features(asset, model)
        frame, selected_series = self._prediction_frame(asset, requested_horizon, series, features)
        missing = [feature for feature in features if feature not in frame.columns]
        if missing:
            raise ProductionAssetInvalidError(f"Required model features are missing: {', '.join(missing[:10])}")
        predictions = np.asarray(model.predict(frame[features]), dtype=float)
        predictions = np.maximum(predictions, 0)
        result = frame[[asset.timestamp, asset.target]].copy()
        result["prediction"] = predictions
        if asset.id == "rossmann":
            result = result.groupby(asset.timestamp, as_index=False)[[asset.target, "prediction"]].sum()
        result = result.sort_values(asset.timestamp)
        points = [
            ProductionPrediction(
                timestamp=pd.Timestamp(row[asset.timestamp]).to_pydatetime(),
                prediction=float(row["prediction"]),
                actual=float(row[asset.target]) if pd.notna(row[asset.target]) else None,
            )
            for _, row in result.iterrows()
        ]
        if not points:
            raise ProductionAssetInvalidError("No eligible held-out prediction rows are available")
        return ProductionForecastResponse(
            dataset=asset.id,
            dataset_name=asset.name,
            model_name=asset.model_name,
            model_type=asset.model_type,
            model_checksum=self._checksum(self._path(asset.model_relative)),
            prediction_kind="held_out_test",
            target=asset.target,
            frequency=asset.frequency,
            series=selected_series,
            horizon=len(points),
            rows_used=len(frame),
            prediction_start=points[0].timestamp,
            prediction_end=points[-1].timestamp,
            predictions=points,
            metrics=self._selected_metrics(asset),
            runtime_ms=round((time.perf_counter() - started) * 1000),
            model_loaded_from_disk=loaded_from_disk,
            generated_at=datetime.now(UTC),
        )

    def report(self, dataset: str) -> ProductionReportResponse:
        asset = self._asset(dataset)
        comparisons = self._comparisons(asset)
        return ProductionReportResponse(
            dataset=asset.id,
            selected_model=asset.model_name,
            selected_metrics=self._selected_metrics(asset),
            comparisons=comparisons,
        )

    def _summary(self, asset: ForecastAsset) -> ProductionDatasetSummary:
        return ProductionDatasetSummary(
            id=asset.id,
            name=asset.name,
            model_name=asset.model_name,
            model_type=asset.model_type,
            target=asset.target,
            frequency=asset.frequency,
            default_horizon=asset.default_horizon,
            model_available=self._path(asset.model_relative).is_file(),
            data_available=self._path(asset.data_relative).is_file(),
        )

    def _asset(self, dataset: str) -> ForecastAsset:
        normalized = dataset.strip().casefold().replace("-", "_")
        if normalized not in ASSETS:
            raise ProductionAssetNotFoundError(f"Unknown forecast dataset: {dataset}")
        return ASSETS[normalized]

    def _path(self, relative: str) -> Path:
        path = (self.project_root / relative).resolve()
        if self.project_root != path and self.project_root not in path.parents:
            raise ProductionAssetInvalidError("Configured asset escaped the project root")
        return path

    def _model(self, asset: ForecastAsset) -> tuple[Any, bool]:
        with self._model_lock:
            if asset.id in self._model_cache:
                return self._model_cache[asset.id], False
            path = self._path(asset.model_relative)
            if not path.is_file():
                raise ProductionAssetNotFoundError(f"Model artifact is unavailable for {asset.id}")
            model = joblib.load(path)
            if not callable(getattr(model, "predict", None)):
                raise ProductionAssetInvalidError(f"Model artifact is invalid for {asset.id}")
            self._model_cache[asset.id] = model
            return model, True

    def _features(self, asset: ForecastAsset, model: Any | None = None) -> list[str]:
        if asset.id == "rossmann":
            path = self._path("artifacts/models/rossmann_xgboost_v1/features.json")
            return [str(item) for item in json.loads(path.read_text(encoding="utf-8"))]
        active_model = model or self._model(asset)[0]
        names = getattr(active_model, "feature_names_in_", None)
        if names is None:
            raise ProductionAssetInvalidError(f"Model feature manifest is unavailable for {asset.id}")
        return [str(item) for item in names]

    def _prediction_frame(
        self, asset: ForecastAsset, horizon: int, series: str | None, features: list[str]
    ) -> tuple[pd.DataFrame, str | None]:
        path = self._path(asset.data_relative)
        if not path.is_file():
            raise ProductionAssetNotFoundError(f"Prediction data is unavailable for {asset.id}")
        if asset.id == "rossmann":
            return self._rossmann_frame(path, horizon, features), None
        series_columns = [asset.series_dimension] if asset.series_dimension else []
        columns = list(dict.fromkeys([asset.timestamp, asset.target, *series_columns, *features]))
        frame = (
            pd.read_csv(path, usecols=columns)
            if path.suffix.casefold() == ".csv"
            else pd.read_parquet(path, columns=columns)
        )
        frame[asset.timestamp] = pd.to_datetime(frame[asset.timestamp], errors="coerce")
        frame = frame.dropna(subset=[asset.timestamp, *features])
        selected_series: str | None = None
        if asset.series_dimension:
            values = sorted(frame[asset.series_dimension].astype(str).unique())
            if not values:
                raise ProductionAssetInvalidError(f"No series are available for {asset.id}")
            selected_series = series or values[0]
            if selected_series not in values:
                raise ProductionAssetInvalidError(f"Unknown series for {asset.id}: {selected_series}")
            frame = frame.loc[frame[asset.series_dimension].astype(str).eq(selected_series)]
        return frame.sort_values(asset.timestamp).tail(horizon).copy(), selected_series

    def _rossmann_frame(self, path: Path, horizon: int, features: list[str]) -> pd.DataFrame:
        train = pd.read_csv(path, low_memory=False)
        train["Date"] = pd.to_datetime(train["Date"], errors="coerce")
        stores = pd.read_csv(self._path("datasets/raw/rossmann/store.csv"), low_memory=False)
        frame = train.merge(stores, on="Store", how="left", validate="many_to_one")
        frame = frame.loc[frame["Open"].eq(1)].sort_values(["Date", "Store"]).copy()
        frame["Year"] = frame["Date"].dt.year
        frame["Month"] = frame["Date"].dt.month
        frame["Day"] = frame["Date"].dt.day
        frame["WeekOfYear"] = frame["Date"].dt.isocalendar().week.astype(int)
        frame["Quarter"] = frame["Date"].dt.quarter
        frame["IsWeekend"] = (frame["Date"].dt.dayofweek >= 5).astype(int)
        for column in (
            "CompetitionDistance",
            "CompetitionOpenSinceMonth",
            "CompetitionOpenSinceYear",
            "Promo2SinceWeek",
            "Promo2SinceYear",
        ):
            median = frame[column].median()
            frame[column] = frame[column].fillna(0 if pd.isna(median) else median)
        frame = pd.get_dummies(
            frame.assign(
                **{
                    column: frame[column].fillna("Unknown").astype(str)
                    for column in ("StoreType", "Assortment", "StateHoliday", "PromoInterval")
                }
            ),
            columns=["StoreType", "Assortment", "StateHoliday", "PromoInterval"],
            dtype=int,
        )
        for feature in features:
            if feature not in frame:
                frame[feature] = 0
        dates = frame["Date"].drop_duplicates().sort_values().tail(horizon)
        return frame.loc[frame["Date"].isin(dates)].copy()

    def _series_values(self, asset: ForecastAsset, path: Path) -> list[str]:
        if path.suffix.casefold() != ".parquet" or not asset.series_dimension:
            return []
        frame = pd.read_parquet(path, columns=[asset.series_dimension])
        return sorted(frame[asset.series_dimension].astype(str).unique())

    def _comparisons(self, asset: ForecastAsset) -> list[dict[str, float | str]]:
        path = self._path(asset.report_relative)
        if not path.is_file():
            raise ProductionAssetNotFoundError(f"Metrics report is unavailable for {asset.id}")
        if asset.id == "rossmann":
            payload = json.loads(path.read_text(encoding="utf-8"))
            metrics = payload.get("xgboost_metrics", {})
            return [{"Model": "xgboost", **{str(key): float(value) for key, value in metrics.items()}}]
        if path.suffix.casefold() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
        else:
            rows = json.loads(path.read_text(encoding="utf-8"))
        return [
            {str(key): self._metric_value(value) for key, value in row.items() if "Rank" not in str(key)}
            for row in rows
        ]

    def _selected_metrics(self, asset: ForecastAsset) -> dict[str, float]:
        comparisons = self._comparisons(asset)
        selected = next(
            (
                row
                for row in comparisons
                if str(row.get("Model", "")).casefold() in asset.model_name.casefold()
                or asset.model_name.casefold() in str(row.get("Model", "")).casefold()
            ),
            comparisons[0],
        )
        return {
            str(key): float(value)
            for key, value in selected.items()
            if key != "Model" and isinstance(value, (int, float))
        }

    @staticmethod
    def _metric_value(value: Any) -> float | str:
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
        return digest.hexdigest()


@lru_cache
def get_production_forecast_service() -> ProductionForecastService:
    return ProductionForecastService(get_settings())
