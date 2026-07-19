from pathlib import Path
import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from aeon.datasets import load_from_tsf_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "m4_daily"
    / "m4_daily_dataset.tsf"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "m4_daily"
)

OUTPUT_FILE = OUTPUT_DIR / "m4_daily_long.parquet"
SUMMARY_FILE = OUTPUT_DIR / "preprocessing_summary.json"

# Number of time series processed before writing a batch.
BATCH_SIZE = 100


def series_to_long_dataframe(batch: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a batch of M4 series from array format into long format.

    Input:
        One row per series with an array in series_value.

    Output:
        One row per timestamp:
        series_name, timestamp, time_index, value
    """
    frames = []

    for row in batch.itertuples(index=False):
        series_name = str(row.series_name)
        start_timestamp = pd.Timestamp(row.start_timestamp)

        values = np.asarray(row.series_value, dtype=np.float64)
        number_of_values = len(values)

        timestamps = start_timestamp + pd.to_timedelta(
            np.arange(number_of_values),
            unit="D",
        )

        series_frame = pd.DataFrame(
            {
                "series_name": series_name,
                "timestamp": timestamps,
                "time_index": np.arange(
                    number_of_values,
                    dtype=np.int32,
                ),
                "value": values,
            }
        )

        frames.append(series_frame)

    return pd.concat(frames, ignore_index=True)


def main() -> None:
    print("=" * 80)
    print("M4 DAILY DATASET PREPROCESSING")
    print("=" * 80)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"M4 Daily dataset not found:\n{INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove an older output so that rerunning the script
    # does not mix old and new data.
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    print("\nLoading TSF dataset...")

    data, metadata = load_from_tsf_file(INPUT_FILE)

    print("Dataset loaded successfully.")
    print(f"Number of series: {len(data):,}")
    print(f"Frequency: {metadata['frequency']}")
    print(f"Forecast horizon: {metadata['forecast_horizon']}")

    total_series = len(data)
    total_observations = 0
    minimum_length = None
    maximum_length = 0

    parquet_writer = None

    try:
        for batch_start in range(0, total_series, BATCH_SIZE):
            batch_end = min(
                batch_start + BATCH_SIZE,
                total_series,
            )

            batch = data.iloc[batch_start:batch_end]
            long_batch = series_to_long_dataframe(batch)

            batch_observations = len(long_batch)
            total_observations += batch_observations

            series_lengths = batch["series_value"].apply(len)

            current_minimum = int(series_lengths.min())
            current_maximum = int(series_lengths.max())

            if minimum_length is None:
                minimum_length = current_minimum
            else:
                minimum_length = min(
                    minimum_length,
                    current_minimum,
                )

            maximum_length = max(
                maximum_length,
                current_maximum,
            )

            arrow_table = pa.Table.from_pandas(
                long_batch,
                preserve_index=False,
            )

            if parquet_writer is None:
                parquet_writer = pq.ParquetWriter(
                    OUTPUT_FILE,
                    arrow_table.schema,
                    compression="snappy",
                )

            parquet_writer.write_table(arrow_table)

            print(
                f"Processed series "
                f"{batch_start + 1:,}–{batch_end:,} "
                f"of {total_series:,} | "
                f"rows written: {total_observations:,}"
            )

    finally:
        if parquet_writer is not None:
            parquet_writer.close()

    if not OUTPUT_FILE.exists():
        raise RuntimeError(
            "The processed Parquet file was not created."
        )

    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)

    summary = {
        "dataset": "M4 Daily",
        "frequency": metadata["frequency"],
        "forecast_horizon": int(
            metadata["forecast_horizon"]
        ),
        "number_of_series": int(total_series),
        "total_observations": int(total_observations),
        "minimum_series_length": int(minimum_length),
        "maximum_series_length": int(maximum_length),
        "processed_file": str(OUTPUT_FILE),
        "processed_file_size_mb": round(file_size_mb, 2),
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(summary, file, indent=4)

    print("\n" + "=" * 80)
    print("PREPROCESSING COMPLETED")
    print("=" * 80)

    print(f"\nTotal series       : {total_series:,}")
    print(f"Total observations : {total_observations:,}")
    print(f"Minimum length     : {minimum_length:,}")
    print(f"Maximum length     : {maximum_length:,}")
    print(f"Output size        : {file_size_mb:.2f} MB")

    print("\nProcessed dataset saved to:")
    print(OUTPUT_FILE)

    print("\nSummary saved to:")
    print(SUMMARY_FILE)

    print("\nProcessed data structure:")
    print(
        pd.read_parquet(OUTPUT_FILE)
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()