from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = PROJECT_ROOT / "reports" / "integration"
BASE_URL = os.environ.get("CAUSALCAST_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def _wait_for_health(client: httpx.Client) -> dict[str, Any]:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            response = client.get("/health")
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Backend health endpoint did not become ready at {BASE_URL}")


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=180) as client:
        health = _wait_for_health(client)
        login = client.post("/api/v1/auth/login/developer")
        login.raise_for_status()
        token = login.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"

        docs = client.get("/docs")
        docs.raise_for_status()
        catalog = client.get("/api/v1/forecast-datasets")
        catalog.raise_for_status()
        models = client.get("/api/v1/production-models")
        models.raise_for_status()

        forecast_path = REPORT_ROOT / "real_forecast_validation.json"
        forecasts = _read(forecast_path)
        for item in forecasts:
            metadata = client.get(f"/api/v1/forecast-datasets/{item['dataset']}/metadata")
            metadata.raise_for_status()
            report = client.get(f"/api/v1/reports/{item['dataset']}")
            report.raise_for_status()
            payload: dict[str, Any] = {
                "dataset": item["dataset"],
                "horizon": min(5, item["horizon"]),
            }
            if item.get("series"):
                payload["series"] = item["series"]
            started = time.perf_counter()
            response = client.post("/api/v1/forecast", json=payload)
            response.raise_for_status()
            value = response.json()
            item.update(
                {
                    "api_validation_pending": False,
                    "api_prediction_status": "passed",
                    "api_http_status": response.status_code,
                    "api_horizon": value["horizon"],
                    "api_first_five_predictions": [point["prediction"] for point in value["predictions"][:5]],
                    "api_runtime_ms": round((time.perf_counter() - started) * 1000),
                }
            )
        _write(forecast_path, forecasts)
        forecast_lines = [
            "# Real forecast validation",
            "",
            "All values below were executed from existing trained artifacts over authentic held-out rows.",
            "They are estimates, not guaranteed future outcomes.",
            "",
            "| Dataset | Model | Direct status | API status | API horizon | API first five predictions |",
            "|---|---|---|---|---:|---|",
        ]
        for item in forecasts:
            predictions = ", ".join(f"{value:.4f}" for value in item["api_first_five_predictions"])
            forecast_lines.append(
                f"| {item['dataset_name']} | {item['model']} | {item['prediction_status']} | "
                f"{item['api_prediction_status']} ({item['api_http_status']}) | {item['api_horizon']} | {predictions} |"
            )
        (REPORT_ROOT / "real_forecast_validation.md").write_text("\n".join(forecast_lines) + "\n", encoding="utf-8")

        # The forecast validation report is eligible project knowledge. Refresh
        # after writing it so the persisted index matches the final report bytes.
        reindex = client.post("/api/v1/reindex", json={"force": False})
        reindex.raise_for_status()
        reindex_result = reindex.json()

        rag_path = REPORT_ROOT / "rag_validation.json"
        rag = _read(rag_path)
        rag.update(
            {
                "indexed_document_count": reindex_result["document_count"],
                "chunk_count": reindex_result["chunk_count"],
                "embedding_dimension": reindex_result["embedding_dimension"],
                "embedded_chunks": reindex_result["embedded_chunks"],
                "reused_chunks": reindex_result["reused_chunks"],
            }
        )
        chat = client.post(
            "/api/v1/chat",
            json={
                "question": "Which model performs best for Tourism Quarterly?",
                "stream": False,
            },
        )
        chat.raise_for_status()
        unavailable = client.post(
            "/api/v1/chat",
            json={
                "question": "What is the private launch code for the CausalCast Mars mission?",
                "stream": False,
            },
        )
        unavailable.raise_for_status()
        search = client.post("/api/v1/search", json={"query": "Electricity forecasting metrics"})
        search.raise_for_status()
        documents = client.get("/api/v1/documents")
        documents.raise_for_status()
        rag["api_validation"] = {
            "chat_http_status": chat.status_code,
            "chat_answer": chat.json()["answer"],
            "chat_sources": chat.json()["sources"],
            "unavailable_http_status": unavailable.status_code,
            "unavailable_answer": unavailable.json()["answer"],
            "unavailable_sources": unavailable.json()["sources"],
            "search_http_status": search.status_code,
            "search_result_count": len(search.json()["results"]),
            "document_http_status": documents.status_code,
            "document_count": documents.json()["document_count"],
            "chunk_count": documents.json()["chunk_count"],
        }
        _write(rag_path, rag)
        rag_lines = [
            "# RAG validation",
            "",
            f"- Indexed documents: {rag['indexed_document_count']}",
            f"- Chunks: {rag['chunk_count']}",
            f"- Embedding dimension: {rag['embedding_dimension']}",
            f"- Generator: {rag['generation_provider']}",
            f"- Live chat/search HTTP status: {chat.status_code}/{search.status_code}",
            f"- Live reindex HTTP status: {reindex.status_code}",
            "",
        ]
        for item in rag["questions"]:
            sources = ", ".join(item["answer_sources"]) if item["answer_sources"] else "none"
            rag_lines.extend(
                [
                    f"## {item['question']}",
                    "",
                    item["answer"],
                    "",
                    f"Sources: {sources}",
                    "",
                ]
            )
        (REPORT_ROOT / "rag_validation.md").write_text("\n".join(rag_lines), encoding="utf-8")

        print(
            json.dumps(
                {
                    "base_url": BASE_URL,
                    "health": health.get("status"),
                    "docs_status": docs.status_code,
                    "dataset_count": len(catalog.json()),
                    "model_count": len(models.json()),
                    "forecast_api_passed": len(forecasts),
                    "rag_chat_status": chat.status_code,
                    "rag_search_status": search.status_code,
                    "rag_reindex_status": reindex.status_code,
                    "rag_document_count": documents.json()["document_count"],
                    "rag_chunk_count": documents.json()["chunk_count"],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
