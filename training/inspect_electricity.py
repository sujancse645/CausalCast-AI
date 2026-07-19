from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "electricity"
    / "LD2011_2014.txt"
)

print("=" * 80)
print("ELECTRICITY DATASET INSPECTION")
print("=" * 80)

print(f"\nFile: {DATA_FILE}")
print(f"File exists: {DATA_FILE.exists()}")

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

# Read only the first five rows to avoid loading the full 711 MB file.
df_sample = pd.read_csv(
    DATA_FILE,
    sep=";",
    decimal=",",
    nrows=5
)

print("\nDataset loaded successfully.")

print("\nShape of sample:")
print(df_sample.shape)

print("\nNumber of columns:")
print(len(df_sample.columns))

print("\nFirst 10 column names:")
print(df_sample.columns[:10].tolist())

print("\nLast 10 column names:")
print(df_sample.columns[-10:].tolist())

print("\nSample rows:")
print(df_sample.iloc[:, :8].to_string())

print("\nData types:")
print(df_sample.dtypes.head(10))

print("\nMissing values in sample:")
print(df_sample.isna().sum().head(10))

print("\nInspection completed.")