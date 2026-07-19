from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPORT_DIR = PROJECT_ROOT / "reports" / "electricity"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = REPORT_DIR / "model_comparison.csv"


def main() -> None:
    results = [
        {
            "Model": "XGBoost",
            "MAE": 17161.09,
            "RMSE": 26206.63,
            "R2": 0.9939,
        },
        {
            "Model": "LightGBM",
            "MAE": 17181.74,
            "RMSE": 25892.66,
            "R2": 0.9940,
        },
        {
            "Model": "CatBoost",
            "MAE": 17433.89,
            "RMSE": 26034.25,
            "R2": 0.9940,
        },
    ]

    df = pd.DataFrame(results)

    df["MAE_Rank"] = df["MAE"].rank(method="min")
    df["RMSE_Rank"] = df["RMSE"].rank(method="min")
    df["R2_Rank"] = df["R2"].rank(method="min", ascending=False)

    df["Average_Rank"] = df[
        ["MAE_Rank", "RMSE_Rank", "R2_Rank"]
    ].mean(axis=1)

    df = df.sort_values(
        by=["Average_Rank", "RMSE", "MAE"]
    ).reset_index(drop=True)

    print("=" * 80)
    print("ELECTRICITY MODEL COMPARISON")
    print("=" * 80)

    print(
        df[
            [
                "Model",
                "MAE",
                "RMSE",
                "R2",
                "Average_Rank",
            ]
        ].to_string(index=False)
    )

    best_model = df.iloc[0]["Model"]

    print("\nRecommended best model:")
    print(best_model)

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nComparison report saved:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()