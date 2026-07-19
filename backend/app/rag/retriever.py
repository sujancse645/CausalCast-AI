from __future__ import annotations

import threading
from typing import Any

from app.rag.embeddings import Embedder
from app.rag.metadata import SearchResult
from app.rag.vector_store import FaissVectorStore


class Retriever:
    """Thread-safe search retrieval from the vector store."""

    def __init__(self, store: FaissVectorStore, embedder: Embedder) -> None:
        self.store = store
        self.embedder = embedder
        self._state: Any | None = None
        self._lock = threading.Lock()

    def invalidate(self) -> None:
        with self._lock:
            self._state = None

    def search(
        self,
        query: str,
        top_k: int = 5,
        minimum_similarity: float = 0.25,
        dataset: str | None = None,
        document_type: str | None = None,
    ) -> list[SearchResult]:
        with self._lock:
            if self._state is None:
                self._state = self.store.load()
            state = self._state

        if state.index.ntotal == 0:
            return []

        query_vector = self.embedder.encode([query])

        # FAISS search
        k = min(top_k * 20, state.index.ntotal)
        distances, indices = state.index.search(query_vector, k)

        results: list[SearchResult] = []
        for dist, idx in zip(distances[0], indices[0], strict=True):
            if idx == -1:
                break

            similarity = float(dist)
            if similarity < minimum_similarity:
                continue

            chunk = state.chunks[idx]

            if dataset and chunk.metadata.dataset_name != dataset:
                continue
            if document_type and chunk.metadata.document_type != document_type:
                continue

            results.append(SearchResult(chunk=chunk, similarity=similarity))

            if len(results) >= top_k:
                break

        return results
