# Phase 1 and Phase 2A Architecture

Phase 1 separates presentation, transport, application service, and persistence concerns. The browser fetches only health and system-readiness resources; demo dashboard values are local and explicitly labeled.

```mermaid
flowchart LR
  U[Browser] -->|HTTP :3000| N[Next.js UI]
  N -->|Typed GET requests| F[FastAPI :8000]
  F --> P[Pydantic response schemas]
  F --> S[System service]
  S --> Q[SQLAlchemy engine]
  Q --> D[(SQLite local / PostgreSQL future)]
  A[Alembic] --> D
```

## Frontend/backend interaction

`frontend/lib/api.ts` enforces a five-second timeout and maps failures to a safe unavailable state. TypeScript interfaces mirror Pydantic response models. Browser-facing configuration uses `NEXT_PUBLIC_API_BASE_URL`; no server secret crosses this boundary.

## Database layer

The engine, session factory, dependency, connectivity probe, and dialect label are centralized in `backend/app/core/database.py`. SQLite is the zero-configuration default. The URL-driven engine and SQLAlchemy models support a later PostgreSQL transition. Alembic contains an initial optional internal metadata migration; current endpoints require no business tables.

## Data flow and security boundaries

The browser is untrusted. FastAPI validates configuration and serializes every successful response through a schema. CORS allows configured origins only and rejects wildcards. Unexpected errors are logged server-side and returned as generic messages. Phase 1 has no authentication, uploads, user code execution, ML computation, or sensitive-data workflow.

## Future modules

Data intelligence, forecasting, calibration, causal intelligence, scenario simulation, optimization, and RAG/agent orchestration remain isolated planned modules. They should enter behind versioned schemas and independently testable services.

## Governed ingestion flow

```mermaid
flowchart LR
  U[Untrusted user file] --> UI[Accessible frontend upload]
  UI -->|multipart stream| API[FastAPI dataset route]
  API --> V[Extension, MIME, size validation]
  V --> T[Generated temporary file + SHA-256]
  T --> D{Duplicate?}
  D -->|yes| C[Cleanup + typed 409]
  D -->|no| P[Bounded CSV parser]
  P --> R[(UUID raw storage)]
  P --> M[(Dataset metadata in SQL)]
  M --> O[Typed metadata + preview]
  R -->|archive| A[Isolated archive storage]
```

The storage service resolves a configured root, accepts only generated filenames, checks containment, streams 1 MB chunks, and cleans temporary or committed files after validation/database failure. Parsing uses Python's CSV module without DataFrames or full-file memory loading. Preview rows are bounded derived metadata; the immutable raw file remains authoritative. Database rows store relative keys only, while response schemas omit all internal keys and stored names.

Trust boundaries are explicit: browser validation is convenience only; the backend is authoritative. CSV content is never executed or rendered as HTML. Archiving moves the raw object before marking its row archived, with restoration on metadata transaction failure. Malware scanning, authentication, authorization, and cloud object storage remain future controls.
