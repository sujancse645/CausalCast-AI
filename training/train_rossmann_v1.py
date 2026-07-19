from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from xgboost import XGBRegressor


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "datasets" / "raw" / "rossmann"
TRAIN_PATH = DATA_DIR / "train.csv"
STORE_PATH = DATA_DIR / "store.csv"

ARTIFACT_DIR = (
    PROJECT_ROOT
    / "artifacts"
    / "models"
    / "rossmann_xgboost_v1"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "rossmann_xgboost_v1"
)


def load_data() -> pd.DataFrame:
    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Missing: {TRAIN_PATH}")

    if not STORE_PATH.exists():
        raise FileNotFoundError(f"Missing: {STORE_PATH}")

    print("Loading train.csv...")
    train = pd.read_csv(TRAIN_PATH, low_memory=False)

    print("Loading store.csv...")
    stores = pd.read_csv(STORE_PATH, low_memory=False)

    train["Date"] = pd.to_datetime(
        train["Date"],
        errors="coerce",
    )

    if train["Date"].isna().any():
        raise ValueError("Invalid dates were found.")

    print("Merging train.csv and store.csv...")

    data = train.merge(
        stores,
        on="Store",
        how="left",
        validate="many_to_one",
    )

    return data


def prepare_features(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()

    # Closed stores have zero sales.
    # For the first model, train only using open stores.
    data = data[data["Open"] == 1].copy()

    data = data.sort_values(
        ["Date", "Store"]
    ).reset_index(drop=True)

    print("Creating date features...")

    data["Year"] = data["Date"].dt.year
    data["Month"] = data["Date"].dt.month
    data["Day"] = data["Date"].dt.day
    data["WeekOfYear"] = (
        data["Date"]
        .dt
        .isocalendar()
        .week
        .astype(int)
    )
    data["Quarter"] = data["Date"].dt.quarter
    data["IsWeekend"] = (
        data["Date"].dt.dayofweek >= 5
    ).astype(int)

    # Handle missing numeric store information.
    numeric_fill_columns = [
        "CompetitionDistance",
        "CompetitionOpenSinceMonth",
        "CompetitionOpenSinceYear",
        "Promo2SinceWeek",
        "Promo2SinceYear",
    ]

    for column in numeric_fill_columns:
        if column in data.columns:
            median_value = data[column].median()

            if pd.isna(median_value):
                median_value = 0

            data[column] = data[column].fillna(
                median_value
            )

    # Handle missing categorical values.
    categorical_columns = [
        "StoreType",
        "Assortment",
        "StateHoliday",
        "PromoInterval",
    ]

    for column in categorical_columns:
        if column in data.columns:
            data[column] = (
                data[column]
                .fillna("Unknown")
                .astype(str)
            )

    print("Encoding categorical columns...")

    data = pd.get_dummies(
        data,
        columns=[
            column
            for column in categorical_columns
            if column in data.columns
        ],
        dtype=int,
    )

    return data


def split_by_time(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unique_dates = sorted(data["Date"].unique())

    train_index = int(len(unique_dates) * 0.70)
    validation_index = int(len(unique_dates) * 0.85)

    train_end = unique_dates[train_index]
    validation_end = unique_dates[validation_index]

    train_data = data[
        data["Date"] < train_end
    ].copy()

    validation_data = data[
        (data["Date"] >= train_end)
        & (data["Date"] < validation_end)
    ].copy()

    test_data = data[
        data["Date"] >= validation_end
    ].copy()

    print("\nTIME-BASED SPLIT")
    print("=" * 60)

    print(
        "Training:",
        train_data["Date"].min(),
        "to",
        train_data["Date"].max(),
        f"({len(train_data):,} rows)",
    )

    print(
        "Validation:",
        validation_data["Date"].min(),
        "to",
        validation_data["Date"].max(),
        f"({len(validation_data):,} rows)",
    )

    print(
        "Testing:",
        test_data["Date"].min(),
        "to",
        test_data["Date"].max(),
        f"({len(test_data):,} rows)",
    )

    return train_data, validation_data, test_data


def calculate_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = mean_absolute_error(
        actual,
        predicted,
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted,
        )
    )

    r2 = r2_score(
        actual,
        predicted,
    )

    denominator = (
        np.abs(actual)
        + np.abs(predicted)
    )

    smape = np.mean(
        200
        * np.abs(predicted - actual)
        / np.maximum(denominator, 1e-8)
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "smape": float(smape),
        "r2": float(r2),
    }


def main() -> None:
    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = load_data()

    print(f"Rows after merging: {len(data):,}")

    data = prepare_features(data)

    print(
        f"Rows after preprocessing: {len(data):,}"
    )

    train_data, validation_data, test_data = (
        split_by_time(data)
    )

    excluded_columns = {
        "Sales",
        "Customers",
        "Date",
    }

    feature_columns = [
        column
        for column in data.columns
        if column not in excluded_columns
        and pd.api.types.is_numeric_dtype(
            data[column]
        )
    ]

    print(
        f"\nNumber of model features: "
        f"{len(feature_columns)}"
    )

    X_train = train_data[feature_columns]
    y_train = train_data["Sales"]

    X_validation = validation_data[
        feature_columns
    ]
    y_validation = validation_data["Sales"]

    X_test = test_data[feature_columns]
    y_test = test_data["Sales"]

    # Simple baseline:
    # predict the average sales from training data.
    baseline_value = float(y_train.mean())

    baseline_predictions = np.full(
        len(y_test),
        baseline_value,
    )

    baseline_metrics = calculate_metrics(
        y_test.to_numpy(),
        baseline_predictions,
    )

    print("\nTraining XGBoost model...")

    model = XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=8,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        eval_metric="rmse",
        tree_method="hist",
        random_state=42,
        n_jobs=-1,
    )

    start_time = time.perf_counter()

    model.fit(
        X_train,
        y_train,
        eval_set=[
            (
                X_validation,
                y_validation,
            )
        ],
        verbose=False,
    )

    training_seconds = (
        time.perf_counter() - start_time
    )

    print(
        f"Training finished in "
        f"{training_seconds:.2f} seconds."
    )

    predictions = model.predict(X_test)

    # Sales cannot be negative.
    predictions = np.maximum(
        predictions,
        0,
    )

    xgboost_metrics = calculate_metrics(
        y_test.to_numpy(),
        predictions,
    )

    print("\nBASELINE METRICS")
    print("=" * 60)
    print(
        json.dumps(
            baseline_metrics,
            indent=2,
        )
    )

    print("\nXGBOOST METRICS")
    print("=" * 60)
    print(
        json.dumps(
            xgboost_metrics,
            indent=2,
        )
    )

    champion = (
        "xgboost"
        if xgboost_metrics["rmse"]
        < baseline_metrics["rmse"]
        else "mean_baseline"
    )

    print(f"\nSelected champion: {champion}")

    print("\nSaving model and reports...")

    joblib.dump(
        model,
        ARTIFACT_DIR / "model.joblib",
    )

    with open(
        ARTIFACT_DIR / "features.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_columns,
            file,
            indent=2,
        )

    metadata = {
        "model_name": "rossmann_xgboost_v1",
        "model_type": "XGBRegressor",
        "dataset": "Rossmann Store Sales",
        "target": "Sales",
        "training_rows": len(train_data),
        "validation_rows": len(
            validation_data
        ),
        "test_rows": len(test_data),
        "training_seconds": training_seconds,
        "baseline_metrics": baseline_metrics,
        "xgboost_metrics": xgboost_metrics,
        "champion": champion,
        "random_seed": 42,
    }

    with open(
        ARTIFACT_DIR / "metadata.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )

    result = test_data[
        [
            "Date",
            "Store",
            "Sales",
            "Promo",
        ]
    ].copy()

    result["Prediction"] = predictions

    result["AbsoluteError"] = np.abs(
        result["Sales"]
        - result["Prediction"]
    )

    result.to_csv(
        REPORT_DIR / "test_predictions.csv",
        index=False,
    )

    daily_result = (
        result.groupby(
            "Date",
            as_index=False,
        )[["Sales", "Prediction"]]
        .sum()
        .sort_values("Date")
    )

    plt.figure(figsize=(14, 6))

    plt.plot(
        daily_result["Date"],
        daily_result["Sales"],
        label="Actual Sales",
    )

    plt.plot(
        daily_result["Date"],
        daily_result["Prediction"],
        label="Predicted Sales",
    )

    plt.xlabel("Date")
    plt.ylabel("Sales")
    plt.title(
        "Rossmann Actual vs Predicted Sales"
    )
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        REPORT_DIR
        / "actual_vs_predicted.png",
        dpi=160,
    )

    plt.close()

    feature_importance = pd.DataFrame(
        {
            "Feature": feature_columns,
            "Importance": (
                model.feature_importances_
            ),
        }
    ).sort_values(
        "Importance",
        ascending=False,
    )

    feature_importance.to_csv(
        REPORT_DIR
        / "feature_importance.csv",
        index=False,
    )

    print("\nTRAINING COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(
        "Model:",
        ARTIFACT_DIR / "model.joblib",
    )
    print(
        "Metadata:",
        ARTIFACT_DIR / "metadata.json",
    )
    print(
        "Predictions:",
        REPORT_DIR / "test_predictions.csv",
    )
    print(
        "Chart:",
        REPORT_DIR / "actual_vs_predicted.png",
    )
    print(
        "Feature importance:",
        REPORT_DIR / "feature_importance.csv",
    )


if __name__ == "__main__":
    main()