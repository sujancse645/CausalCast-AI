# CausalCast AI

## Phase 2D — Governed Time-Series Preparation

Phase 2D converts immutable CSV uploads into versioned prepared CSV artifacts after confirmed-schema and data-quality gates. The deterministic pipeline aligns hourly, daily, weekly, monthly, or quarterly periods; applies semantic aggregation; records duplicate and generated periods; creates shifted target lags and rolling features; adds calendar and trend features; excludes unsafe same-period target-derived metrics; and assigns chronological train, validation, test, and expanding-window fold boundaries.

Artifacts and JSON manifests are private under `data/processed/prepared/<uuid>/`. Every manifest records source checksum, schema and quality versions, configuration, feature lineage, split boundaries, and artifact checksum. CSV is the supported Phase 2D output; Parquet, business-day calendars, advanced categorical transforms, and model training are deferred. Apply migrations with `cd backend; ..\.venv\Scripts\python.exe -m alembic upgrade head`.

**Probabilistic Revenue Forecasting and Marketing Decision Intelligence Platform**

*Predict. Explain. Simulate. Optimize. Decide.*

CausalCast AI is designed to help e-commerce marketing teams make uncertainty-aware revenue and budget decisions. Phase 1 provides the production foundation. Phase 2A adds governed CSV ingestion, immutable raw storage, technical metadata, bounded previews, dataset APIs, and an accessible dataset library. It does not perform schema inference, quality scoring, forecasting, causal inference, optimization, RAG, or agent work.

## Architecture and stack

The Next.js App Router frontend calls a versioned FastAPI API through a typed client. FastAPI uses Pydantic v2 settings and response models; SQLAlchemy 2 connects to local SQLite and remains PostgreSQL-compatible. Alembic owns migrations. Docker Compose runs isolated frontend and backend services with a persistent database volume.

- Frontend: Next.js, React, TypeScript, Tailwind CSS, Recharts, Lucide, Vitest, Testing Library
- Backend: Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic, Pytest, Ruff, MyPy
- Delivery: Docker, Docker Compose, GitHub Actions, PowerShell scripts

## Repository structure

```text
backend/       FastAPI application, database, migration, and tests
frontend/      Next.js command center and component tests
data/          ignored raw, processed, and synthetic data areas
docs/          architecture, API, and roadmap documents
scripts/       Windows setup, start, and validation automation
.github/       continuous integration workflow
```

## Prerequisites

- Python 3.11 or newer
- Node.js 20.9 or newer and npm
- Docker Desktop (optional)

## Windows PowerShell setup

From the repository root:

```powershell
.\scripts\setup.ps1
.\scripts\start-dev.ps1
```

The scripts use `npm.cmd`, avoiding PowerShell execution-policy issues with `npm.ps1`.

## Manual backend setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-dev.txt
Set-Location .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Apply all database migrations before using dataset APIs:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m alembic upgrade head
# Or, from the repository root:
Set-Location ..
.\scripts\migrate.ps1
```

## Manual frontend setup

```powershell
Set-Location .\frontend
npm.cmd install
npm.cmd run dev
```

Copy `.env.example` files to `.env` only when overriding defaults. The public frontend variable contains a browser-visible API origin and must never contain secrets.

## Docker setup

```powershell
docker compose config
docker compose up --build
docker compose down
```

The browser uses `http://localhost:8000`, not a container-only hostname. Compose waits for backend health before starting the frontend.

## Environment variables

Backend variables include the application settings plus `DATASET_STORAGE_ROOT`, upload/quarantine/archive directory names, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_DATASET_EXTENSIONS`, preview/column limits, ingestion version, and archive delete mode. The frontend uses `NEXT_PUBLIC_API_BASE_URL`. See the root and service `.env.example` files for exact defaults.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | API identity |
| GET | `/health` | Service and database health |
| GET | `/api/v1/system/info` | Typed platform readiness |
| POST | `/api/v1/datasets/upload` | Stream and validate a CSV upload |
| GET | `/api/v1/datasets` | Paginated dataset library |
| GET | `/api/v1/datasets/stats` | Real active-dataset summary |
| GET | `/api/v1/datasets/{id}` | Dataset technical metadata |
| GET | `/api/v1/datasets/{id}/preview` | Bounded stored preview |
| DELETE | `/api/v1/datasets/{id}` | Archive a dataset |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

## Testing and code quality

Run the complete suite:

```powershell
.\scripts\test-all.ps1
```

Or run commands individually:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m ruff format --no-cache --check .
..\.venv\Scripts\python.exe -m ruff check --no-cache .
..\.venv\Scripts\python.exe -m mypy app
..\.venv\Scripts\python.exe -m pytest

Set-Location ..\frontend
npm.cmd run format:check
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```

## Roadmap

Phase 1, Phase 2A, Phase 2B, and Phase 2C are complete. Phase 2D will add governed time-series preparation and immutable derived features. See [the development roadmap](docs/development-roadmap.md).

## Phase 2A ingestion behavior

- Supported format: CSV (`.csv`) only. XLSX is pending.
- Default maximum: 25 MB, enforced while streaming in 1 MB chunks rather than trusting `Content-Length`.
- CSV encodings: UTF-8/BOM, UTF-8, Windows-1252, and Latin-1 fallback; delimiters: comma, semicolon, tab, and pipe.
- Stored files use UUID-generated names under `data/raw/uploads`; archived files move to `data/raw/archived`.
- SHA-256 duplicates return HTTP 409 and do not create another record or physical copy.
- Previews are persisted as bounded derived metadata (20 rows by default, 500 characters per cell). Raw files remain immutable.
- The included `data/synthetic/sample_marketing_data.csv` is small synthetic demonstration data, not real business data.

Manual upload from PowerShell:

```powershell
curl.exe -F "file=@data/synthetic/sample_marketing_data.csv;type=text/csv" http://localhost:8000/api/v1/datasets/upload
```

## Troubleshooting

- If `npm` is blocked by PowerShell policy, use `npm.cmd` as shown above.
- If the UI reports the API unavailable, confirm the backend is on port 8000 and `CORS_ORIGINS` includes `http://localhost:3000`.
- SQLite URLs are relative to the process working directory; start the backend from `backend/`.
- Docker Desktop may need to be started before Compose build or up commands work.
- HTTP 409 means the exact file checksum already exists; use the returned dataset UUID.
- HTTP 413 means the streamed upload exceeded `MAX_UPLOAD_SIZE_MB`; HTTP 415 means extension or MIME validation failed.

## Security

No authentication is claimed yet. Uploads are untrusted, streamed, size-limited, extension/MIME/CSV-structure validated, stored with generated names, and never executed. This is format validation—not antivirus or content-disarm scanning. Errors do not expose storage paths or production tracebacks. Do not use this phase with sensitive production data until authentication, authorization, malware scanning, and retention controls are added.

## Phase 2B — Intelligent schema mapping

Phase 2B profiles a bounded CSV sample locally and proposes an explainable semantic role for each column. Physical types and semantic meanings remain separate. Every proposal includes deterministic confidence, structured evidence, alternatives, and ambiguity warnings. Proposals are derived metadata: raw uploads are never changed, no data is sent to external AI, and a person must confirm mappings before future phases use them.

Confidence combines normalized-name evidence, physical-type compatibility, bounded distribution signals, and ROAS/CTR/CPC/CPA/conversion-rate relationships where available. Configure it with the documented `SCHEMA_INFERENCE_*` environment variables. Automatic confirmation is deliberately disabled.

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
$datasetId = "<dataset-uuid>"
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/datasets/$datasetId/schema/infer" -ContentType "application/json" -Body '{"force_reinfer":true,"reason":"manual review"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/datasets/$datasetId/schema"
```

Confirmation requires a date/timestamp and a target candidate; unresolved columns must be mapped or ignored. Phase 2B does not assess full data quality, clean data, or establish forecasting readiness.

## Phase 2C — Data Quality Intelligence

Phase 2C performs a local, deterministic, bounded scan of immutable CSV uploads using the active reviewed schema. It reports completeness, uniqueness, validity, consistency, temporal integrity, robust IQR outliers, cardinality, metric relationships, and carefully labelled leakage risks. Reports are versioned derived metadata; no values are imputed, deleted, corrected, or exported.

Dimension scores start at 100. Blockers deduct 50, errors 20, warnings 7, and informational findings 1 from the relevant dimension. Overall weights are completeness 15%, uniqueness 10%, validity 20%, consistency 15%, temporal 15%, integrity 10%, and leakage safety 15%. Any blocker caps the result at `DATA_QUALITY_SCORE_BLOCKER_CAP`. `quality_ready` means ready for governed preparation, never forecast-ready.

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
$datasetId = "<dataset-uuid>"
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/datasets/$datasetId/quality/analyze" -ContentType "application/json" -Body '{"force_reanalyze":true}'
Invoke-RestMethod "http://localhost:8000/api/v1/datasets/$datasetId/quality/findings?page=1&page_size=20"
```

All `DATA_QUALITY_*` thresholds are environment-configurable. Scans disclose coverage and retain only bounded evidence. Business-key duplicates, outliers, and name-based leakage signals require human review.

## License

License to be selected before public distribution.
