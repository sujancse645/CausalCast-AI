from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.rag.dependencies import get_rag_service  # noqa: E402
from app.rag.document_registry import DocumentRegistry  # noqa: E402
from app.services.production_forecast_service import (  # noqa: E402
    ASSETS,
    get_production_forecast_service,
)

REPORT_ROOT = PROJECT_ROOT / "reports" / "integration"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def validate_forecasts() -> list[dict[str, Any]]:
    service = get_production_forecast_service()
    results: list[dict[str, Any]] = []
    for dataset, asset in ASSETS.items():
        response = service.forecast(dataset)
        results.append(
            {
                "dataset": dataset,
                "dataset_name": asset.name,
                "input_source": asset.data_relative,
                "model": response.model_name,
                "model_type": response.model_type,
                "model_file": asset.model_relative,
                "metrics_file": asset.report_relative,
                "model_checksum": response.model_checksum,
                "model_load_status": "loaded",
                "prediction_status": "passed",
                "prediction_kind": response.prediction_kind,
                "rows_used": response.rows_used,
                "series": response.series,
                "horizon": response.horizon,
                "prediction_start": response.prediction_start.isoformat(),
                "prediction_end": response.prediction_end.isoformat(),
                "first_five_predictions": [point.prediction for point in response.predictions[:5]],
                "runtime_ms": response.runtime_ms,
                "model_loaded_from_disk": response.model_loaded_from_disk,
                "api_validation_pending": True,
                "metrics": response.metrics,
            }
        )
    _write_json(REPORT_ROOT / "real_forecast_validation.json", results)
    lines = [
        "# Real forecast validation",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "All results are predictions over held-out real test rows, not guaranteed future outcomes.",
        "",
        "| Dataset | Model | Rows | Horizon | Period | First five predictions | Runtime ms |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    for item in results:
        values = ", ".join(f"{value:.4f}" for value in item["first_five_predictions"])
        lines.append(
            f"| {item['dataset_name']} | {item['model']} | {item['rows_used']} | {item['horizon']} | "
            f"{item['prediction_start']} to {item['prediction_end']} | {values} | {item['runtime_ms']} |"
        )
    (REPORT_ROOT / "real_forecast_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results


def validate_rag() -> dict[str, Any]:
    registry = DocumentRegistry(PROJECT_ROOT)
    candidates: list[Path] = [PROJECT_ROOT / "README.md"] if (PROJECT_ROOT / "README.md").is_file() else []
    for directory_name in ("docs", "reports"):
        directory = PROJECT_ROOT / directory_name
        if directory.is_dir():
            candidates.extend(path for path in directory.rglob("*") if path.is_file())
    entries = registry.entries()
    started = time.perf_counter()
    service = get_rag_service()
    index = service.reindex(force=False)
    indexing_runtime_ms = round((time.perf_counter() - started) * 1000)

    questions = [
        "Which model performs best for Tourism Quarterly?",
        "What are the Electricity forecasting metrics?",
        "Which datasets are supported?",
        "How does the forecasting API work?",
        "What is the architecture of the RAG system?",
        "What is the private launch code for the CausalCast Mars mission?",
    ]
    validations: list[dict[str, Any]] = []
    for question in questions:
        started = time.perf_counter()
        result = service.chat(question)
        validations.append(
            {
                "question": question,
                "answer": result.answer,
                "answer_sources": result.sources,
                "retrieved_sources": [item.chunk.metadata.source for item in result.results],
                "similarities": [round(item.similarity, 6) for item in result.results],
                "runtime_ms": round((time.perf_counter() - started) * 1000),
            }
        )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "discovered_document_count": len(candidates),
        "indexed_document_count": index.document_count,
        "skipped_document_count": len(candidates) - len(entries),
        "chunk_count": index.chunk_count,
        "embedding_dimension": index.embedding_dimension,
        "embedded_chunks": index.embedded_chunks,
        "reused_chunks": index.reused_chunks,
        "index_path": "backend/storage/vector_db/index.faiss",
        "metadata_path": "backend/storage/vector_db/metadata.pkl",
        "indexing_runtime_ms": indexing_runtime_ms,
        "generation_provider": "deterministic_grounded_fallback",
        "flan_t5_runtime_status": "not_integrated",
        "questions": validations,
    }
    _write_json(REPORT_ROOT / "rag_validation.json", payload)
    lines = [
        "# RAG validation",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        f"- Discovered files: {payload['discovered_document_count']}",
        f"- Indexed documents: {payload['indexed_document_count']}",
        f"- Skipped files: {payload['skipped_document_count']}",
        f"- Chunks: {payload['chunk_count']}",
        f"- Embedding dimension: {payload['embedding_dimension']}",
        f"- Indexing runtime: {payload['indexing_runtime_ms']} ms",
        "- Generator: deterministic grounded fallback (FLAN-T5 is not integrated in the active runtime)",
        "",
    ]
    for item in validations:
        lines.extend(
            [
                f"## {item['question']}",
                "",
                item["answer"],
                "",
                f"Sources: {', '.join(item['answer_sources']) if item['answer_sources'] else 'none'}",
                "",
            ]
        )
    (REPORT_ROOT / "rag_validation.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def main() -> None:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    forecasts = validate_forecasts()
    rag = validate_rag()
    print(
        json.dumps(
            {
                "forecast_datasets": len(forecasts),
                "rag_documents": rag["indexed_document_count"],
                "rag_chunks": rag["chunk_count"],
                "embedding_dimension": rag["embedding_dimension"],
                "generated_files": sorted(path.relative_to(PROJECT_ROOT).as_posix() for path in REPORT_ROOT.iterdir()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
