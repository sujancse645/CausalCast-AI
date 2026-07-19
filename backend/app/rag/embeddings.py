from __future__ import annotations

from typing import Any, Protocol

import numpy as np


class Embedder(Protocol):
    @property
    def model_name(self) -> str: ...

    @property
    def dimension(self) -> int: ...

    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Lazy, normalized sentence-transformer encoder."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", batch_size: int = 32) -> None:
        self._model_name = model_name
        self.batch_size = batch_size
        self._model: Any | None = None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        model = self._load()
        dimension_getter = getattr(model, "get_embedding_dimension", model.get_sentence_embedding_dimension)
        dimension = dimension_getter()
        if not dimension:
            raise RuntimeError("Embedding model did not report a dimension")
        return int(dimension)

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)
        values = self._load().encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        vectors = np.asarray(values, dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return np.asarray(vectors / np.maximum(norms, np.finfo(np.float32).eps), dtype=np.float32)

    def _load(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            try:
                self._model = SentenceTransformer(self._model_name, local_files_only=True)
            except OSError:
                self._model = SentenceTransformer(self._model_name)
        return self._model
