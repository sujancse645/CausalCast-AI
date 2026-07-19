from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "electricity"
    / "LD2011_2014.txt"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "electricity"
)

OUTPUT_FILE = OUTPUT_DIR / "electricity_hourly.csv"


def main() -> None:
    print("=" * 80)
    print("ELECTRICITY DATASET PREPROCESSING")
    print("=" * 80)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input dataset not found: {INPUT_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nLoading full dataset...")
    print("This may take a few minutes because the file is about 711 MB.")

    df = pd.read_csv(
        INPUT_FILE,
        sep=";",
        decimal=",",
        parse_dates=[0],
        low_memory=False,
    )

    print("\nOriginal shape:")
    print(df.shape)

    # Rename timestamp column.
    df = df.rename(columns={df.columns[0]: "timestamp"})

    # Set timestamp as index.
    df = df.set_index("timestamp")

    # Ensure meter columns are numeric.
    df = df.apply(pd.to_numeric, errors="coerce")

    print("\nMissing values before cleaning:")
    print(int(df.isna().sum().sum()))

    # Replace missing values with zero.
    df = df.fillna(0)

    print("\nResampling 15-minute readings into hourly totals...")

    # Sum four 15-minute readings into one hourly consumption value.
    hourly = df.resample("1h").sum()

    # Create an aggregate system-wide electricity load.
    hourly["total_load"] = hourly.sum(axis=1)

    print("\nHourly shape:")
    print(hourly.shape)

    print("\nDate range:")
    print("Start:", hourly.index.min())
    print("End:  ", hourly.index.max())

    print("\nFirst five rows:")
    print(hourly[["total_load"]].head())

    print("\nSaving processed dataset...")
    hourly.to_csv(OUTPUT_FILE)

    print("\nSaved successfully:")
    print(OUTPUT_FILE)

    print("\nPreprocessing completed.")


if __name__ == "__main__":
    main()