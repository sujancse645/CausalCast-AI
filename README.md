# CausalCast AI

CausalCast AI is a full-stack forecasting and decision-intelligence platform built with FastAPI, Next.js, governed time-series pipelines, trained tree models, explainability services, business-intelligence foundations, and a local document-grounded RAG assistant.

Forecasts shown by the production integration are executed from checksum-verified model artifacts over genuine held-out project data. They are estimates, not guaranteed future outcomes. RAG answers are restricted to indexed project documents and return an explicit unavailable response when evidence is absent.

## Current capabilities

- Immutable, bounded CSV ingestion with UUID identifiers, schema review, data-quality gates, and chronological preparation.
- Baseline, gradient-boosting, and N-HiTS forecasting infrastructure with persisted metrics and checksums.
- Read-only inference adapters for five existing real-data model/dataset pairs.
- Explainability and diagnostics foundations; feature contribution is never presented as causality.
- Executive/operations BI foundations that display unavailable states instead of fabricated values.
- Local RAG using `all-MiniLM-L6-v2`, cosine FAISS retrieval, source citations, SSE streaming, and a deterministic grounded generator.
- Typed FastAPI and frontend contracts, RBAC middleware, audit/governance foundations, Docker, Kustomize, and Helm manifests.

## Architecture

```text
Next.js UI -> typed API client -> authenticated FastAPI routes
                                      |-> governed forecasting services -> external model/data assets
                                      |-> RAG retriever -> FAISS + document metadata
                                      |-> SQLAlchemy metadata -> Alembic-managed database
```

The production forecast page is `/forecasts`; the project assistant is `/copilot`. Long-lived raw/model artifacts are not committed to Git.

## Validated forecasting assets

| Dataset               | Selected model | Held-out metric evidence                   |
| --------------------- | -------------- | ------------------------------------------ |
| Rossmann Store Sales  | XGBoost        | RMSE 1535.3397; MAE 1102.3380              |
| Electricity Load      | LightGBM       | RMSE 25892.66; MAE 17181.74; R2 0.994      |
| M4 Daily              | LightGBM       | RMSE 516.3444; sMAPE 1.3426; R2 0.9908     |
| Online Retail II      | XGBoost        | RMSE 21559.3180; MAE 13350.9277            |
| Tourism yearly source | XGBoost        | RMSE 123264.0997; sMAPE 16.3418; R2 0.9743 |

Tourism is yearly in the repository source metadata; it is not relabelled as quarterly. Detailed executed predictions are in `reports/integration/real_forecast_validation.*` after validation.

## Local installation

Requirements: Python 3.11+, Node.js 20.9+ (Node 24 is used by the frontend image), and npm.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
Set-Location frontend
npm ci
Set-Location ..
Copy-Item .env.example .env
```

Place model and data assets as described in [data and model assets](docs/data-and-model-assets.md), then migrate and index:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe scripts\index_rag.py
```

Start the services in separate terminals:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
Set-Location frontend
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

Local endpoints:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

See [local development](docs/local-development.md) for environment and troubleshooting details.

## API

Key authenticated routes include:

| Method | Path                                           | Purpose                                       |
| ------ | ---------------------------------------------- | --------------------------------------------- |
| GET    | `/health`                                      | Database-backed health                        |
| GET    | `/api/v1/production-models`                    | Available inference models                    |
| GET    | `/api/v1/forecast-datasets`                    | Available model/data pairs                    |
| GET    | `/api/v1/forecast-datasets/{dataset}/metadata` | Feature, series, horizon, metric contract     |
| POST   | `/api/v1/forecast`                             | Execute a real held-out forecast              |
| GET    | `/api/v1/reports/{dataset}`                    | Selected comparison metrics                   |
| POST   | `/api/v1/chat`                                 | Grounded answer or exact unavailable fallback |
| POST   | `/api/v1/search`                               | Top-K semantic retrieval                      |
| GET    | `/api/v1/documents`                            | Indexed document inventory                    |
| POST   | `/api/v1/reindex`                              | Authorized incremental reindex                |

Complete contracts are documented in [API reference](docs/api.md) and Swagger.

## RAG

The registry indexes `README.md`, `docs/`, and appropriate `reports/` Markdown, text, JSON, and CSV files. It excludes environments, raw/processed/features datasets, models, caches, and self-referential RAG validation reports. Chunks are 800 characters with 150-character overlap. Embeddings are normalized 384-dimensional `all-MiniLM-L6-v2` vectors stored in FAISS with checksum-verified metadata and an incremental cache.

The active answer provider is deterministic and grounded. A local FLAN-T5 generator is not integrated into the active runtime. See [RAG architecture](docs/RAG.md).

## Environment

Copy example files; never commit `.env` files. Important variables include `APP_ENV`, `DATABASE_URL`, `CORS_ORIGINS`, `SECRET_KEY`, `PROJECT_ROOT`, `MODEL_ROOT`, `DATA_ROOT`, `REPORTS_ROOT`, `RAG_PROJECT_ROOT`, `RAG_STORAGE_ROOT`, `HF_HOME`, and `NEXT_PUBLIC_API_BASE_URL`. Production must supply a stable secret and a real identity integration; the development-token route is disabled in production.

## Quality commands

```powershell
Set-Location backend
$env:PYTHONPYCACHEPREFIX="$env:TEMP\causalcast-pyc"
..\.venv\Scripts\python.exe -m compileall -q app
..\.venv\Scripts\python.exe -m ruff format --check --no-cache app tests
..\.venv\Scripts\python.exe -m ruff check --no-cache app tests
..\.venv\Scripts\python.exe -m mypy app --explicit-package-bases --cache-dir "$env:TEMP\causalcast-mypy"
..\.venv\Scripts\python.exe -m pytest -q -o cache_dir="$env:TEMP\causalcast-pytest"

Set-Location ..\frontend
npm run format:check
npm run lint
npm run typecheck
npm run test
npm run build
npx playwright test e2e/production-integration.spec.ts --project=chromium
```

## Deployment and live links

Docker/Compose, Kubernetes/Kustomize, and Helm configuration is present. A live frontend/backend URL is intentionally not listed: deployment is blocked until the exposed historical JWT fallback is rotated/remediated, production authentication is configured, and authentic model/data assets are provisioned on supported persistent storage. See [deployment](docs/deployment.md).

## Screenshots

No screenshots are committed in this release. The responsive production forecast and RAG flows are exercised by Playwright rather than represented by unverified images.

## Known limitations

- Public deployment is not yet validated.
- Large authentic data/model artifacts require external provisioning and integrity verification.
- The active RAG generator is deterministic; FLAN-T5 is not active.
- Inventory, supply-chain, geographic, and revenue-specific BI remain unavailable unless legitimate source data is configured.
- PDF/email delivery providers are not configured.
- Phase 5 explainability contains foundations; unsupported diagnostics must remain visibly unavailable.

## License

A distribution license has not yet been selected.
