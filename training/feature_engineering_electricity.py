from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "electricity"
    / "electricity_hourly.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "features"
    / "electricity"
)

OUTPUT_FILE = OUTPUT_DIR / "electricity_features.csv"


def main() -> None:
    print("=" * 80)
    print("ELECTRICITY FEATURE ENGINEERING")
    print("=" * 80)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nLoading hourly dataset...")

    # Load only the timestamp and aggregate target.
    # Individual meter columns are intentionally excluded to prevent leakage.
    df = pd.read_csv(
        INPUT_FILE,
        usecols=["timestamp", "total_load"],
        parse_dates=["timestamp"],
    )

    df = (
        df.sort_values("timestamp")
        .drop_duplicates(subset=["timestamp"])
        .reset_index(drop=True)
    )

    print("Original shape:", df.shape)

    # Calendar features
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["day_of_month"] = df["timestamp"].dt.day
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    df["week_of_year"] = df["timestamp"].dt.isocalendar().week.astype(int)
    df["month"] = df["timestamp"].dt.month
    df["quarter"] = df["timestamp"].dt.quarter
    df["year"] = df["timestamp"].dt.year
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Lag features: only past target values
    lag_hours = [1, 2, 3, 6, 12, 24, 48, 72, 168, 336]

    for lag in lag_hours:
        df[f"lag_{lag}"] = df["total_load"].shift(lag)

    # Rolling statistics must be shifted first.
    # This prevents the current target value from entering its own features.
    past_load = df["total_load"].shift(1)

    for window in [3, 6, 12, 24, 48, 168]:
        df[f"rolling_mean_{window}"] = past_load.rolling(window).mean()
        df[f"rolling_std_{window}"] = past_load.rolling(window).std()
        df[f"rolling_min_{window}"] = past_load.rolling(window).min()
        df[f"rolling_max_{window}"] = past_load.rolling(window).max()

    # Change-based features from past observations
    df["change_1h"] = df["lag_1"] - df["lag_2"]
    df["change_24h"] = df["lag_24"] - df["lag_48"]

    df = df.dropna().reset_index(drop=True)

    print("Final shape:", df.shape)
    print("Number of model features:", len(df.columns) - 2)

    print("\nColumns:")
    print(df.columns.tolist())

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nFeature dataset saved:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()