from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "electricity"
    / "electricity_hourly_dataset.ts"
)

print("=" * 80)
print("First 20 lines of the file")
print("=" * 80)

with open(FILE, "r", encoding="utf-8", errors="ignore") as f:
    for i in range(20):
        line = f.readline()
        if not line:
            break
        print(f"{i+1:02d}: {line.rstrip()}")