# N-HiTS forecasting

CausalCast uses NeuralForecast 3.1.x for N-HiTS. Training consumes only checksum-verified Phase 2D prepared datasets whose deep-readiness snapshot passed. Governed panel data maps to `unique_id`, `ds`, and `y`, with separately classified historical, future-known, and static covariates.

`NHiTSConfig` validates YAML configuration for horizon, input size, stacks, blocks, hidden size/layers, dropout, activation, learning rate, optimizer, scheduler, weight decay, batching, early stopping, accelerator, devices, determinism, and seed. Mixed precision is enabled only for CUDA.

Validation is chronological. Training uses only train rows, metrics use executed predictions for the following validation horizon, and final test rows remain untouched.

## API

- `POST /api/v1/deep/train/nhits`
- `GET /api/v1/deep/train/status`
- `GET /api/v1/deep/experiments`
- `GET /api/v1/deep/experiments/{id}`
- `POST /api/v1/deep/checkpoint/resume`

Training is synchronous. Clients should use an appropriate timeout and can query persisted status afterward.
