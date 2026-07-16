# API Reference

Base URL for local development: `http://localhost:8000`. All timestamps use ISO 8601 UTC serialization.

## `GET /`

```json
{"name":"CausalCast AI API","message":"CausalCast AI backend is running","version":"0.1.0","docs":"/docs","health":"/health"}
```

## `GET /health`

Returns HTTP 200 while the database is reachable and HTTP 503 with `status: degraded` otherwise.

```json
{"status":"healthy","service":"causalcast-backend","version":"0.1.0","environment":"development","timestamp":"2026-07-15T12:00:00Z"}
```

## `GET /api/v1/system/info`

```json
{
  "application":{"name":"CausalCast AI","version":"0.1.0","environment":"development"},
  "backend":{"framework":"FastAPI","status":"operational"},
  "database":{"type":"SQLite","status":"connected"},
  "modules":{"data_intelligence":"planned","forecasting":"planned","causal_intelligence":"planned","simulation":"planned","optimization":"planned","rag_copilot":"planned"}
}
```

Unknown routes return FastAPI's typed JSON 404 response. Interactive OpenAPI documentation is at `/docs`; ReDoc is at `/redoc`.

## Dataset ingestion endpoints

`POST /api/v1/datasets/upload` accepts one multipart field named `file`. Successful CSV ingestion returns HTTP 201 with the public UUID, normalized original filename, size, SHA-256, row/column counts, ordered headers, delimiter, encoding, status, timestamps, warnings, and at most the configured preview rows. Internal filenames and storage paths are never returned.

```powershell
curl.exe -F "file=@data/synthetic/sample_marketing_data.csv;type=text/csv" http://localhost:8000/api/v1/datasets/upload
```

`GET /api/v1/datasets?page=1&page_size=20&status=ready&search=marketing&sort=newest` returns `items` plus pagination metadata. Page size is limited to 100.

`GET /api/v1/datasets/stats` returns the real active count, latest active filename/time, and ingestion status. `GET /api/v1/datasets/{dataset_id}` returns technical metadata. `GET /api/v1/datasets/{dataset_id}/preview?limit=10` returns a bounded ordered preview; archived datasets return 404 for preview. `DELETE /api/v1/datasets/{dataset_id}` moves the raw file to archive storage and returns the archived status and deletion time.

Common errors are typed JSON: 400 empty/invalid header, 409 duplicate checksum with `existing_dataset_id`, 413 streamed size limit, 415 extension/MIME mismatch, 422 malformed CSV structure, 404 unknown/archived resource, and a safe generic 500 for persistence/storage failure.

## Schema mapping endpoints

- `GET /api/v1/schema/roles` lists the stable semantic taxonomy.
- `GET /api/v1/datasets/schema/stats` returns aggregate review statistics.
- `POST /api/v1/datasets/{dataset_id}/schema/infer` creates a new bounded-scan schema version (`201`).
- `GET /api/v1/datasets/{dataset_id}/schema` returns the active profile.
- `GET /api/v1/datasets/{dataset_id}/schema/history` returns retained versions.
- `PATCH /api/v1/datasets/{dataset_id}/schema/columns/{column_profile_id}` records a role override and reason.
- `POST /api/v1/datasets/{dataset_id}/schema/confirm` validates and confirms the active mapping.

Missing resources return `404`, invalid dataset operations `400`, version conflicts `409`, and invalid mappings or confirmation `422`. Responses omit stored filenames and paths.
