# Data and model assets

## Git policy

Authentic datasets, trained model binaries, generated FAISS artifacts, caches, and raw uploads are intentionally excluded from normal Git history. The following roots are ignored:

- `datasets/`
- `models/`
- `artifacts/` except its placeholder
- `backend/storage/vector_db/`
- Hugging Face, Python, Node, Next.js, test, and CatBoost caches

Compact executed validation reports under `reports/integration/` are allowed. They contain model checksums and bounded predictions, not full datasets.

## Required local layout

| Dataset          | Model artifact                                      | Inference data                                           | Metrics                                              |
| ---------------- | --------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------- |
| Rossmann         | `artifacts/models/rossmann_xgboost_v1/model.joblib` | `datasets/raw/rossmann/train.csv` plus `store.csv`       | `artifacts/models/rossmann_xgboost_v1/metadata.json` |
| Electricity      | `models/electricity/lightgbm_electricity.pkl`       | `datasets/features/electricity/electricity_features.csv` | `reports/electricity/model_comparison.csv`           |
| M4 Daily         | `models/m4_daily/lightgbm_m4.pkl`                   | `datasets/training/m4_daily/m4_test.parquet`             | `reports/m4_daily/model_comparison.json`             |
| Online Retail II | `models/online_retail/xgboost_model.pkl`            | `datasets/training/online_retail/test.parquet`           | `reports/online_retail/model_comparison.json`        |
| Tourism yearly   | `models/tourism/xgboost_model.pkl`                  | `datasets/training/tourism/test.parquet`                 | `reports/tourism/model_comparison.json`              |

The executed model SHA-256 values are recorded in `reports/integration/real_forecast_validation.json`. The service recomputes model checksums and uses only allowlisted project-relative paths. Joblib/pickle files must come from this trusted training pipeline; never load an uploaded or user-selected pickle.

## Large files observed locally

The release audit observed authentic assets up to approximately 891 MB (M4 features), 678 MB (raw Electricity), 184 MB (processed Electricity), and 164 MB (M4 training). These exceed normal GitHub source-repository strategy and some deployment ephemeral-disk limits.

No upstream download URLs or object-storage bucket are configured in this repository, so the project does not invent one. Provision assets from the original governed workspace or an approved artifact store, preserving folder layout and recording SHA-256 checksums.

## Verification

```powershell
Get-FileHash artifacts\models\rossmann_xgboost_v1\model.joblib -Algorithm SHA256
Get-FileHash models\electricity\lightgbm_electricity.pkl -Algorithm SHA256
Get-FileHash models\m4_daily\lightgbm_m4.pkl -Algorithm SHA256
Get-FileHash models\online_retail\xgboost_model.pkl -Algorithm SHA256
Get-FileHash models\tourism\xgboost_model.pkl -Algorithm SHA256
.\.venv\Scripts\python.exe scripts\validate_integration.py
```

For a hosted demonstration, a small representative subset may be derived from the authentic source, versioned with its source checksum and selection rule, and clearly labelled. No such deployment subset has been generated or claimed yet.
