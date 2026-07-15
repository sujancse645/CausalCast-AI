# CausalCast AI

**Probabilistic Revenue Forecasting and Marketing Decision Intelligence Platform**

*Predict. Explain. Simulate. Optimize. Decide.*

CausalCast AI is designed to help e-commerce marketing teams make uncertainty-aware revenue and budget decisions. Phase 1 is a production-oriented foundation only: it provides the application shell, API, database plumbing, health monitoring, tests, CI, containers, and documentation. It does not perform forecasting, causal inference, optimization, RAG, or agent work.

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

Migrations are ready but are not required for the health-only application. To create the internal metadata table:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m alembic upgrade head
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

Backend variables are `APP_NAME`, `APP_VERSION`, `APP_ENV`, `DEBUG`, `API_V1_PREFIX`, `BACKEND_HOST`, `BACKEND_PORT`, `DATABASE_URL`, `CORS_ORIGINS`, and `LOG_LEVEL`. The frontend uses `NEXT_PUBLIC_API_BASE_URL`. See the root and service `.env.example` files for local defaults.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | API identity |
| GET | `/health` | Service and database health |
| GET | `/api/v1/system/info` | Typed platform readiness |
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

Phase 1 establishes the foundation. Later phases add data intelligence, probabilistic forecasting, trust and calibration, causal intelligence, scenario simulation, risk-aware optimization, evidence-grounded copilot workflows, and deployment hardening. See [the development roadmap](docs/development-roadmap.md).

## Troubleshooting

- If `npm` is blocked by PowerShell policy, use `npm.cmd` as shown above.
- If the UI reports the API unavailable, confirm the backend is on port 8000 and `CORS_ORIGINS` includes `http://localhost:3000`.
- SQLite URLs are relative to the process working directory; start the backend from `backend/`.
- Docker Desktop may need to be started before Compose build or up commands work.

## Security

No authentication is claimed in Phase 1. The API accepts no files or executable input, errors do not expose production tracebacks, wildcard credentialed CORS is rejected, and no credentials are stored. Do not use this phase with sensitive production data.

## License

License to be selected before public distribution.
