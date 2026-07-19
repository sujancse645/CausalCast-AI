# Deployment

## Current release status

Local production build and browser integration pass. Public deployment has not been executed. Three prerequisites remain:

1. Rotate and remediate the JWT fallback that exists in historical commit `19d3cb6` before pushing.
2. Configure production identity; `/auth/login/developer` is intentionally disabled in production.
3. Provision authentic model/data/report/FAISS assets on supported persistent storage with checksum verification.

Do not publish a URL until health, forecast, RAG, CORS, browser console, and backend logs are verified on that exact deployment.

## Practical target

- Frontend: Vercel or the existing standalone Next.js Docker image.
- Backend: a container platform with persistent disk and sufficient memory, such as Render/Railway only after account, plan, disk, and artifact limits are confirmed.
- Database: managed PostgreSQL for production; SQLite is local/isolated validation only.
- Assets: approved object storage or persistent disk. Large training tables need not be deployed when bounded authentic inference inputs are sufficient.

No provider authentication or billing authorization is available in the current environment, so provider resources were not created.

## Environment contract

Backend production variables:

```text
APP_ENV=production
DATABASE_URL=<provider secret>
SECRET_KEY=<new stable rotated secret>
CORS_ORIGINS=https://<frontend-domain>
PROJECT_ROOT=/project-assets
MODEL_ROOT=/project-assets/models
DATA_ROOT=/project-assets/datasets
REPORTS_ROOT=/project-assets/reports
RAG_PROJECT_ROOT=/project-assets
RAG_STORAGE_ROOT=/data/vector_db
HF_HOME=/data/huggingface
LOG_LEVEL=INFO
```

Frontend build variable:

```text
NEXT_PUBLIC_API_BASE_URL=https://<backend-domain>
```

Never place secrets in `NEXT_PUBLIC_*` variables. Build again after setting the final backend origin and verify that production JavaScript contains no localhost API origin.

## Commands

Backend start:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Local Compose validation:

```powershell
docker compose config --quiet
docker compose build
docker compose up
```

The Docker Engine must be running. The Compose development profile mounts the local authentic `models/`, `artifacts/`, `datasets/`, `reports/`, `docs/`, and `README.md` read-only beneath `/project-assets`; the FAISS/database volume remains writable. A remote deployment must provision equivalent verified assets on persistent storage rather than relying on source-control inclusion. Set `APP_ENV=production`, a stable rotated `SECRET_KEY`, provider database URL, final CORS origin, and final frontend build API URL explicitly for production.

Kustomize validation:

```powershell
kubectl kustomize deployment/kubernetes/base
kubectl kustomize deployment/kubernetes/overlays/production
```

Helm validation (when Helm is installed):

```powershell
helm lint deployment/helm/causalcast -f deployment/helm/causalcast/values-production.yaml
helm template causalcast deployment/helm/causalcast -f deployment/helm/causalcast/values-production.yaml
```

## Post-deployment gate

Validate `/health`, `/docs` if intentionally exposed, every configured forecast asset, RAG retrieval/fallback, frontend forecast/RAG UI, CORS, browser console, server exceptions, and README links. Record only executed results.
