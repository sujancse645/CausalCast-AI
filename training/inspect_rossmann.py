from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "datasets" / "raw" / "rossmann"

TRAIN_PATH = DATA_DIR / "train.csv"
STORE_PATH = DATA_DIR / "store.csv"


def main() -> None:
    print("Checking files...")

    if not TRAIN_PATH.exists():
        raise FileNotFoundError(f"Missing file: {TRAIN_PATH}")

    if not STORE_PATH.exists():
        raise FileNotFoundError(f"Missing file: {STORE_PATH}")

    train = pd.read_csv(TRAIN_PATH, low_memory=False)
    stores = pd.read_csv(STORE_PATH, low_memory=False)

    print("\nROSSMANN TRAIN DATA")
    print("=" * 60)
    print(f"Rows and columns: {train.shape}")
    print(f"Columns: {train.columns.tolist()}")

    print("\nFirst five rows:")
    print(train.head())

    print("\nMissing values:")
    print(train.isna().sum().sort_values(ascending=False))

    train["Date"] = pd.to_datetime(train["Date"], errors="coerce")

    print("\nDate range:")
    print(f"Start date: {train['Date'].min()}")
    print(f"End date: {train['Date'].max()}")

    print("\nSales summary:")
    print(train["Sales"].describe())

    print("\nNumber of stores:")
    print(train["Store"].nunique())

    print("\nSTORE DATA")
    print("=" * 60)
    print(f"Rows and columns: {stores.shape}")
    print(f"Columns: {stores.columns.tolist()}")

    print("\nStore missing values:")
    print(stores.isna().sum().sort_values(ascending=False))

    print("\nDataset inspection completed successfully.")


if __name__ == "__main__":
    main()