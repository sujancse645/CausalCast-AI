from pathlib import Path
from aeon.datasets import load_from_tsf_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "m4_daily"
    / "m4_daily_dataset.tsf"
)

print("=" * 80)
print("M4 DAILY DATASET INSPECTION")
print("=" * 80)

print(DATA)

data, metadata = load_from_tsf_file(DATA)

print("\nMetadata")
print(metadata)

print("\nNumber of Series")
print(len(data))

print("\nColumns")
print(data.columns)

print("\nFirst 5 Series")
print(data.head())