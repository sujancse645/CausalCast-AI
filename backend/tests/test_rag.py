from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.rag.chunker import SemanticChunker
from app.rag.dependencies import get_rag_service
from app.rag.document_registry import DocumentRegistry
from app.rag.loader import ProjectDocumentLoader
from app.rag.metadata import DocumentMetadata, SourceDocument
from app.rag.rag_service import UNAVAILABLE_ANSWER, RAGService


class TestEmbedder:
    model_name = "test-token-embedder"
    dimension = 64

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in text.casefold().replace("_", " ").split():
                index = int(hashlib.sha256(token.strip(".,:;()[]").encode()).hexdigest()[:8], 16) % self.dimension
                vectors[row, index] += 1
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, np.finfo(np.float32).eps)


def project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "reports" / "tourism").mkdir(parents=True)
    (tmp_path / "reports" / "integration").mkdir(parents=True)
    (tmp_path / "datasets" / "raw").mkdir(parents=True)
    (tmp_path / "README.md").write_text("# CausalCast\n\nProject forecasting documentation.", encoding="utf-8")
    (tmp_path / "docs" / "api.md").write_text(
        "# API\n\nPOST /api/v1/chat answers project questions.\n\n## Search\nPOST /api/v1/search retrieves chunks.",
        encoding="utf-8",
    )
    (tmp_path / "reports" / "tourism" / "model_comparison.csv").write_text(
        "Model,RMSE,MAE\nxgboost,12.5,8\nlightgbm,20,10\n",
        encoding="utf-8",
    )
    (tmp_path / "reports" / "tourism" / "metrics.json").write_text(
        json.dumps({"dataset": "tourism", "metric": "RMSE"}), encoding="utf-8"
    )
    (tmp_path / "reports" / "integration" / "real_forecast_validation.json").write_text(
        json.dumps(
            [
                {"dataset": "tourism", "dataset_name": "Tourism (yearly source)"},
                {"dataset": "electricity", "dataset_name": "Electricity Load"},
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "reports" / "integration" / "rag_validation.json").write_text(
        json.dumps({"question": "feedback must not be indexed"}), encoding="utf-8"
    )
    (tmp_path / "datasets" / "raw" / "secret.csv").write_text("secret,value\nx,1\n", encoding="utf-8")
    return tmp_path


def service(tmp_path: Path) -> RAGService:
    root = project(tmp_path / "project")
    value = RAGService(root, tmp_path / "vectors", embedder=TestEmbedder())
    value.reindex()
    return value


def test_loader_indexes_allowlisted_sources_and_metadata(tmp_path: Path) -> None:
    root = project(tmp_path)
    registry = DocumentRegistry(root)
    entries = registry.entries()
    assert {entry.source for entry in entries} == {
        "README.md",
        "docs/api.md",
        "reports/tourism/metrics.json",
        "reports/tourism/model_comparison.csv",
        "reports/integration/real_forecast_validation.json",
    }
    documents = ProjectDocumentLoader(registry).load_all()
    tourism = next(item for item in documents if item.metadata.source.endswith("model_comparison.csv"))
    assert tourism.metadata.dataset_name == "tourism"
    assert tourism.metadata.document_type == "csv"
    assert tourism.metadata.timestamp and tourism.metadata.checksum


def test_chunker_enforces_size_overlap_and_section_metadata() -> None:
    content = "First semantic sentence. " * 80
    metadata = DocumentMetadata("docs/test.md", "Metrics", None, "markdown", "2026-01-01", "abc")
    chunks = SemanticChunker(800, 150).chunk(SourceDocument(content, metadata))
    assert len(chunks) > 1
    assert all(len(chunk.content) <= 800 for chunk in chunks)
    assert chunks[0].end_character - chunks[1].start_character >= 100
    assert all(chunk.metadata.section_title == "Metrics" for chunk in chunks)


def test_embeddings_are_normalized_persisted_and_incrementally_reused(tmp_path: Path) -> None:
    value = service(tmp_path)
    state = value.store.load()
    query = value.embedder.encode(["tourism xgboost"])
    assert np.linalg.norm(query[0]) == pytest.approx(1.0)
    assert state.dimension == 64 and state.index.ntotal == len(state.chunks)
    assert (tmp_path / "vectors" / "index.faiss").is_file()
    assert (tmp_path / "vectors" / "metadata.pkl").is_file()
    second = value.reindex()
    assert second.embedded_chunks == 0
    assert second.reused_chunks == second.chunk_count


def test_retrieval_filters_and_grounded_chat(tmp_path: Path) -> None:
    value = service(tmp_path)
    hits = value.search("tourism model RMSE", dataset="tourism", document_type="csv", minimum_similarity=0)
    assert hits and all(hit.chunk.metadata.dataset_name == "tourism" for hit in hits)
    answer = value.chat("Which model has the best RMSE for Tourism?", minimum_similarity=0)
    assert "xgboost" in answer.answer and "12.5" in answer.answer
    assert answer.sources == ["reports/tourism/model_comparison.csv"]
    metrics = value.chat("What are the Tourism forecasting metrics?", minimum_similarity=0)
    assert "RMSE 12.5" in metrics.answer and "MAE 8" in metrics.answer
    supported = value.chat("Which datasets are supported?", minimum_similarity=0)
    assert "Tourism (yearly source)" in supported.answer and "Electricity Load" in supported.answer
    assert supported.sources == ["reports/integration/real_forecast_validation.json"]
    unavailable = value.chat("Explain quantum entanglement", minimum_similarity=0)
    assert unavailable.answer == UNAVAILABLE_ANSWER and unavailable.sources == []


def test_chat_search_documents_and_reindex_endpoints(client: TestClient, tmp_path: Path) -> None:
    value = service(tmp_path)
    app.dependency_overrides[get_rag_service] = lambda: value
    try:
        token_response = client.post("/api/v1/auth/login/developer")
        assert token_response.status_code == 200
        headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}
        search_response = client.post(
            "/api/v1/search",
            json={"query": "tourism RMSE", "dataset": "tourism", "minimum_similarity": 0},
            headers=headers,
        )
        assert search_response.status_code == 200
        assert search_response.json()["results"][0]["metadata"]["source"].startswith("reports/tourism")
        chat_response = client.post(
            "/api/v1/chat",
            json={"question": "Which model has the best RMSE for Tourism?", "minimum_similarity": 0},
            headers=headers,
        )
        assert chat_response.status_code == 200
        assert chat_response.json()["sources"] == ["reports/tourism/model_comparison.csv"]
        documents_response = client.get("/api/v1/documents", headers=headers)
        assert documents_response.status_code == 200 and documents_response.json()["document_count"] == 5
        reindex_response = client.post("/api/v1/reindex", json={"force": False}, headers=headers)
        assert reindex_response.status_code == 200 and reindex_response.json()["reused_chunks"] > 0
    finally:
        app.dependency_overrides.pop(get_rag_service, None)
