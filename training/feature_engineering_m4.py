from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "m4_daily"
    / "m4_daily_long.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "features"
    / "m4_daily"
)

OUTPUT_FILE = OUTPUT_DIR / "m4_features.parquet"


def create_features(group: pd.DataFrame) -> pd.DataFrame:

    group = group.sort_values("timestamp").copy()

    # -------------------------------------------------
    # Calendar Features
    # -------------------------------------------------

    group["year"] = group["timestamp"].dt.year
    group["month"] = group["timestamp"].dt.month
    group["day"] = group["timestamp"].dt.day
    group["weekday"] = group["timestamp"].dt.weekday
    group["quarter"] = group["timestamp"].dt.quarter

    # -------------------------------------------------
    # Lag Features
    # -------------------------------------------------

    lags = [1, 2, 3, 7, 14, 28]

    for lag in lags:
        group[f"lag_{lag}"] = group["value"].shift(lag)

    # -------------------------------------------------
    # Rolling Mean
    # -------------------------------------------------

    past = group["value"].shift(1)

    for window in [7, 14, 28]:

        group[f"rolling_mean_{window}"] = (
            past.rolling(window).mean()
        )

        group[f"rolling_std_{window}"] = (
            past.rolling(window).std()
        )

        group[f"rolling_min_{window}"] = (
            past.rolling(window).min()
        )

        group[f"rolling_max_{window}"] = (
            past.rolling(window).max()
        )

    return group


def main():

    print("=" * 80)
    print("M4 FEATURE ENGINEERING")
    print("=" * 80)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("\nLoading parquet...")

    df = pd.read_parquet(INPUT_FILE)

    print(df.shape)

    print("\nGenerating features...")

    df = (
        df.groupby("series_name", group_keys=False)
        .apply(create_features)
    )

    print("\nRemoving NaN rows...")

    df = df.dropna()

    print(df.shape)

    print("\nSaving feature dataset...")

    df.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print("\nDone.")

    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()