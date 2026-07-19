from __future__ import annotations

import hashlib
import json
import os
import pickle
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import faiss
import numpy as np

from app.rag.chunker import SemanticChunker
from app.rag.embeddings import Embedder
from app.rag.metadata import DocumentChunk, DocumentInfo, SourceDocument


class VectorStoreIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class IndexBuildResult:
    document_count: int
    chunk_count: int
    embedding_dimension: int
    embedded_chunks: int
    reused_chunks: int


@dataclass(slots=True)
class VectorStoreState:
    index: Any
    chunks: list[DocumentChunk]
    documents: list[DocumentInfo]
    model_name: str
    dimension: int


class FaissVectorStore:
    FILES = ("index.faiss", "metadata.pkl", "embeddings_cache.pkl")

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root.resolve()
        self._lock = threading.RLock()

    @property
    def manifest_path(self) -> Path:
        return self.storage_root / "manifest.json"

    def rebuild(
        self,
        documents: list[SourceDocument],
        chunker: SemanticChunker,
        embedder: Embedder,
        force: bool = False,
    ) -> IndexBuildResult:
        with self._lock:
            chunks = chunker.chunk_documents(documents)
            dimension = embedder.dimension
            cached = {} if force else self._load_embedding_cache(embedder.model_name, dimension)
            missing = [chunk for chunk in chunks if chunk.id not in cached]
            if missing:
                encoded = embedder.encode([chunk.embedding_text for chunk in missing])
                for chunk, vector in zip(missing, encoded, strict=True):
                    cached[chunk.id] = np.asarray(vector, dtype=np.float32)
            vectors = (
                np.vstack([cached[chunk.id] for chunk in chunks]).astype(np.float32)
                if chunks
                else np.empty((0, dimension), dtype=np.float32)
            )
            if vectors.shape != (len(chunks), dimension):
                raise VectorStoreIntegrityError("Embedding matrix shape does not match chunk metadata")
            index = faiss.IndexFlatIP(dimension)
            if len(vectors):
                index.add(vectors)
            document_infos = self._document_infos(documents, chunks)
            active_cache = {chunk.id: cached[chunk.id] for chunk in chunks}
            self._persist(index, chunks, document_infos, active_cache, embedder.model_name, dimension)
            return IndexBuildResult(
                document_count=len(document_infos),
                chunk_count=len(chunks),
                embedding_dimension=dimension,
                embedded_chunks=len(missing),
                reused_chunks=len(chunks) - len(missing),
            )

    def load(self) -> VectorStoreState:
        with self._lock:
            manifest = self._manifest()
            self._verify_files(manifest)
            with (self.storage_root / "metadata.pkl").open("rb") as handle:
                payload = pickle.load(handle)  # noqa: S301 - checksum-verified, application-created artifact
            chunks = [DocumentChunk.from_dict(item) for item in payload["chunks"]]
            documents = [DocumentInfo(**item) for item in payload["documents"]]
            index = faiss.read_index(str(self.storage_root / "index.faiss"))
            if index.ntotal != len(chunks):
                raise VectorStoreIntegrityError("FAISS row count does not match metadata")
            return VectorStoreState(
                index=index,
                chunks=chunks,
                documents=documents,
                model_name=str(payload["model_name"]),
                dimension=int(payload["dimension"]),
            )

    def _load_embedding_cache(self, model_name: str, dimension: int) -> dict[str, np.ndarray]:
        try:
            manifest = self._manifest()
            self._verify_files(manifest)
            with (self.storage_root / "embeddings_cache.pkl").open("rb") as handle:
                payload = pickle.load(handle)  # noqa: S301 - checksum-verified, application-created artifact
            if payload.get("model_name") != model_name or int(payload.get("dimension", 0)) != dimension:
                return {}
            vectors = payload.get("vectors", {})
            if isinstance(vectors, np.ndarray):
                identifiers = payload.get("chunk_ids", [])
                if vectors.shape != (len(identifiers), dimension):
                    return {}
                return {
                    str(identifier): np.asarray(vector, dtype=np.float32)
                    for identifier, vector in zip(identifiers, vectors, strict=True)
                }
            return {
                str(identifier): np.asarray(vector, dtype=np.float32)
                for identifier, vector in vectors.items()
                if np.asarray(vector).shape == (dimension,)
            }
        except (FileNotFoundError, KeyError, ValueError, TypeError, pickle.UnpicklingError, VectorStoreIntegrityError):
            return {}

    def _persist(
        self,
        index: Any,
        chunks: list[DocumentChunk],
        documents: list[DocumentInfo],
        cache: dict[str, np.ndarray],
        model_name: str,
        dimension: int,
    ) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix="rag-index-", dir=self.storage_root))
        try:
            faiss.write_index(index, str(temporary / "index.faiss"))
            with (temporary / "metadata.pkl").open("wb") as handle:
                pickle.dump(
                    {
                        "model_name": model_name,
                        "dimension": dimension,
                        "chunks": [chunk.to_dict() for chunk in chunks],
                        "documents": [document.to_dict() for document in documents],
                    },
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            with (temporary / "embeddings_cache.pkl").open("wb") as handle:
                identifiers = list(cache)
                vectors = (
                    np.vstack([cache[identifier] for identifier in identifiers]).astype(np.float32)
                    if identifiers
                    else np.empty((0, dimension), dtype=np.float32)
                )
                pickle.dump(
                    {
                        "model_name": model_name,
                        "dimension": dimension,
                        "chunk_ids": identifiers,
                        "vectors": vectors,
                    },
                    handle,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            manifest = {
                "version": 1,
                "model_name": model_name,
                "dimension": dimension,
                "document_count": len(documents),
                "chunk_count": len(chunks),
                "files": {name: self._checksum(temporary / name) for name in self.FILES},
            }
            (temporary / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            for name in self.FILES:
                os.replace(temporary / name, self.storage_root / name)
            os.replace(temporary / "manifest.json", self.manifest_path)
        finally:
            for child in temporary.iterdir() if temporary.exists() else []:
                child.unlink(missing_ok=True)
            temporary.rmdir() if temporary.exists() else None

    def _manifest(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(self.manifest_path.read_text(encoding="utf-8")))

    def _verify_files(self, manifest: dict[str, Any]) -> None:
        for name in self.FILES:
            path = self.storage_root / name
            expected = manifest.get("files", {}).get(name)
            if not expected or not path.is_file() or self._checksum(path) != expected:
                raise VectorStoreIntegrityError(f"RAG index artifact failed integrity validation: {name}")

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _document_infos(documents: list[SourceDocument], chunks: list[DocumentChunk]) -> list[DocumentInfo]:
        metadata_by_source = {document.metadata.source: document.metadata for document in documents}
        counts: dict[str, int] = {}
        for chunk in chunks:
            counts[chunk.metadata.source] = counts.get(chunk.metadata.source, 0) + 1
        return [
            DocumentInfo(
                source=source,
                dataset_name=metadata.dataset_name,
                document_type=metadata.document_type,
                timestamp=metadata.timestamp,
                checksum=metadata.checksum,
                chunk_count=counts.get(source, 0),
            )
            for source, metadata in sorted(metadata_by_source.items())
        ]
