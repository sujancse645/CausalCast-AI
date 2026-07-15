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
