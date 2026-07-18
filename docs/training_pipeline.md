# Deep training pipeline

1. Phase 2D creates an immutable, checksummed prepared artifact and chronological manifests.
2. Phase 3C readiness validates frequency, history, covariates, leakage, and windows.
3. Training locks configuration to that snapshot and records `ForecastExperiment` and `ForecastModelRun` rows.
4. N-HiTS fits on train rows and generates validation predictions.
5. MAE, RMSE, MAPE, SMAPE, WAPE, and R² are computed from executed predictions.
6. Checkpoints, configuration, metrics, history, hardware, logs, plots, checksums, and Git commit are persisted under `artifacts/training/<experiment UUID>/<run UUID>`.

CPU is always supported. `auto` selects CUDA, then MPS, then CPU. CUDA alone may use mixed precision. Deterministic mode seeds Python, NumPy, and PyTorch and disables cuDNN benchmarking; equality across different systems is not guaranteed.
