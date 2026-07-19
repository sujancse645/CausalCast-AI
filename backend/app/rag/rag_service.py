from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.rag.chunker import SemanticChunker
from app.rag.document_registry import DocumentRegistry
from app.rag.embeddings import Embedder, SentenceTransformerEmbedder
from app.rag.loader import ProjectDocumentLoader
from app.rag.metadata import DocumentInfo, SearchResult
from app.rag.retriever import Retriever
from app.rag.vector_store import FaissVectorStore, IndexBuildResult

UNAVAILABLE_ANSWER = "I could not find that information in the project."
PROMPT_TEMPLATE = """You are the CausalCast AI project assistant.
Answer the question using only the supplied project context.
Do not use outside knowledge, infer unsupported facts, or invent values.
If the context does not contain the answer, reply exactly:
I could not find that information in the project.

Question:
{question}

Project context:
{context}
"""
TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9_+-]*")
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "does",
    "for",
    "how",
    "in",
    "is",
    "of",
    "the",
    "to",
    "what",
    "which",
    "with",
    "work",
}


@dataclass(frozen=True, slots=True)
class ChatResult:
    answer: str
    sources: list[str]
    results: list[SearchResult]


@dataclass(frozen=True, slots=True)
class GeneratedAnswer:
    text: str
    sources: list[str]


class GroundedAnswerGenerator(Protocol):
    def generate(self, question: str, results: list[SearchResult], project_root: Path) -> GeneratedAnswer: ...


class DeterministicGroundedGenerator:
    """Provider-free fallback that quotes or computes only from retrieved project documents."""

    def generate(self, question: str, results: list[SearchResult], project_root: Path) -> GeneratedAnswer:
        if not results:
            return GeneratedAnswer(UNAVAILABLE_ANSWER, [])
        dataset_catalog = self._supported_datasets(question, results, project_root)
        if dataset_catalog:
            return dataset_catalog
        comparison = self._model_comparison(question, results, project_root)
        if comparison:
            return comparison
        metrics = self._metric_summary(question, results, project_root)
        if metrics:
            return metrics
        query_terms = self._terms(question)
        searchable = " ".join(
            f"{result.chunk.metadata.source} {result.chunk.metadata.dataset_name or ''} {result.chunk.content}"
            for result in results
        ).casefold()
        matched = {term for term in query_terms if term in searchable}
        if query_terms and len(matched) < max(1, min(2, len(query_terms))):
            return GeneratedAnswer(UNAVAILABLE_ANSWER, [])

        candidates: list[tuple[int, float, str, str]] = []
        for result in results:
            for sentence in SENTENCE.split(result.chunk.content):
                clean = sentence.strip().lstrip("#*- ")
                if len(clean) < 20:
                    continue
                terms = self._terms(clean)
                overlap = len(query_terms & terms)
                candidates.append((overlap, result.similarity, clean[:600], result.chunk.metadata.source))
        selected: list[str] = []
        sources: list[str] = []
        for _, _, sentence, source in sorted(candidates, key=lambda item: (item[0], item[1]), reverse=True):
            if sentence not in selected:
                selected.append(sentence)
                if source not in sources:
                    sources.append(source)
            if len(selected) == 3 or sum(map(len, selected)) >= 1200:
                break
        return GeneratedAnswer(" ".join(selected), sources) if selected else GeneratedAnswer(UNAVAILABLE_ANSWER, [])

    def _supported_datasets(
        self, question: str, results: list[SearchResult], project_root: Path
    ) -> GeneratedAnswer | None:
        lowered = question.casefold()
        if "dataset" not in lowered or not ({"support", "supported", "available"} & self._terms(question)):
            return None
        for result in results:
            source = result.chunk.metadata.source
            if not source.endswith("real_forecast_validation.json"):
                continue
            value = self._read_json(project_root, source)
            if not isinstance(value, list):
                continue
            names: list[str] = []
            for item in value:
                if isinstance(item, dict) and item.get("dataset_name"):
                    names.append(str(item["dataset_name"]))
            if names:
                return GeneratedAnswer(f"The validated forecasting datasets are: {', '.join(names)}.", [source])
        return None

    def _metric_summary(self, question: str, results: list[SearchResult], project_root: Path) -> GeneratedAnswer | None:
        if not ({"metric", "metrics", "performance"} & self._terms(question)):
            return None
        query_terms = self._terms(question)
        for result in results:
            source = result.chunk.metadata.source
            if Path(source).stem.casefold() != "model_comparison":
                continue
            dataset = result.chunk.metadata.dataset_name
            if dataset and not (self._terms(dataset) & query_terms):
                continue
            path = self._safe_source_path(project_root, source)
            if path is None:
                continue
            rows = self._comparison_rows(path)
            ranked: list[tuple[dict[str, Any], float | None]] = []
            for row in rows:
                rmse_key = self._metric_key(row, "RMSE")
                ranked.append((row, self._number(row.get(rmse_key)) if rmse_key else None))
            valid = [(row, rmse) for row, rmse in ranked if rmse is not None]
            if not valid:
                continue
            best, _ = min(valid, key=lambda item: item[1])
            model = next((str(value) for key, value in best.items() if key.casefold() == "model"), "best model")
            metrics: list[str] = []
            for name in ("MAE", "RMSE", "R2", "sMAPE", "MAPE", "MASE"):
                key = self._metric_key(best, name)
                value = self._number(best.get(key)) if key else None
                if value is not None:
                    metrics.append(f"{name} {value:g}")
            label = (dataset or "project").replace("_", " ").title()
            return GeneratedAnswer(
                f"For {label}, the lowest-RMSE model is {model}; its reported metrics are {', '.join(metrics)}.",
                [source],
            )
        return None

    def _model_comparison(
        self, question: str, results: list[SearchResult], project_root: Path
    ) -> GeneratedAnswer | None:
        lowered = question.casefold()
        if "best" not in lowered and "lowest" not in lowered and "highest" not in lowered:
            return None
        for result in results:
            source = result.chunk.metadata.source
            if Path(source).stem.casefold() != "model_comparison":
                continue
            path = self._safe_source_path(project_root, source)
            if path is None:
                continue
            rows = self._comparison_rows(path)
            if not rows:
                continue
            metric = self._requested_metric(question, rows)
            candidates = [(row, self._number(row.get(metric))) for row in rows]
            valid = [(row, value) for row, value in candidates if value is not None]
            if not valid:
                continue
            best_row, best_value = (
                max(valid, key=lambda item: item[1])
                if metric.casefold() == "r2"
                else min(valid, key=lambda item: item[1])
            )
            model = next(
                (str(value) for key, value in best_row.items() if key.casefold() == "model"),
                "The leading model",
            )
            dataset = (result.chunk.metadata.dataset_name or "project").replace("_", " ").title()
            direction = "highest" if metric.casefold() == "r2" else "lowest"
            return GeneratedAnswer(
                f"According to the {dataset} model comparison, {model} has the {direction} {metric} ({best_value:g}).",
                [source],
            )
        return None

    @staticmethod
    def _comparison_rows(path: Path) -> list[dict[str, Any]]:
        try:
            if path.suffix.casefold() == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    return [dict(row) for row in csv.DictReader(handle)]
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            return [dict(row) for row in value] if isinstance(value, list) else []
        except (OSError, csv.Error, json.JSONDecodeError, TypeError, ValueError):
            return []

    @staticmethod
    def _requested_metric(question: str, rows: list[dict[str, Any]]) -> str:
        keys = [key for row in rows for key in row]
        for preferred in ("RMSE", "MAE", "sMAPE", "MAPE", "MASE", "R2"):
            if preferred.casefold() in question.casefold():
                return next((key for key in keys if key.casefold() == preferred.casefold()), preferred)
        return next((key for key in keys if key.casefold() == "rmse"), "RMSE")

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _metric_key(row: dict[str, Any], metric: str) -> str | None:
        return next((key for key in row if key.casefold() == metric.casefold()), None)

    @staticmethod
    def _safe_source_path(project_root: Path, source: str) -> Path | None:
        path = (project_root / source).resolve()
        return path if path == project_root or project_root in path.parents else None

    @classmethod
    def _read_json(cls, project_root: Path, source: str) -> Any:
        path = cls._safe_source_path(project_root, source)
        if path is None:
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {
            token.casefold() for token in TOKEN.findall(value) if token.casefold() not in STOPWORDS and len(token) > 1
        }


class RAGService:
    def __init__(
        self,
        project_root: Path,
        storage_root: Path,
        *,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 800,
        overlap: int = 150,
        max_file_bytes: int = 10 * 1024 * 1024,
        max_csv_rows: int = 20_000,
        embedding_batch_size: int = 32,
        embedder: Embedder | None = None,
        generator: GroundedAnswerGenerator | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.registry = DocumentRegistry(self.project_root, max_file_bytes=max_file_bytes)
        self.loader = ProjectDocumentLoader(self.registry, max_csv_rows=max_csv_rows)
        self.chunker = SemanticChunker(chunk_size=chunk_size, overlap=overlap)
        self.embedder = embedder or SentenceTransformerEmbedder(model_name, batch_size=embedding_batch_size)
        self.store = FaissVectorStore(storage_root)
        self.retriever = Retriever(self.store, self.embedder)
        self.generator = generator or DeterministicGroundedGenerator()

    def reindex(self, force: bool = False) -> IndexBuildResult:
        result = self.store.rebuild(self.loader.load_all(), self.chunker, self.embedder, force=force)
        self.retriever.invalidate()
        return result

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        minimum_similarity: float = 0.25,
        dataset: str | None = None,
        document_type: str | None = None,
    ) -> list[SearchResult]:
        return self.retriever.search(query, top_k, minimum_similarity, dataset, document_type)

    def chat(
        self,
        question: str,
        *,
        top_k: int = 5,
        minimum_similarity: float = 0.25,
        dataset: str | None = None,
        document_type: str | None = None,
    ) -> ChatResult:
        retrieval_query = question
        lowered = question.casefold()
        if "dataset" in lowered and any(term in lowered for term in ("support", "available")):
            retrieval_query += " real forecast validation dataset_name supported model input_source"
        results = self.search(
            retrieval_query,
            top_k=top_k,
            minimum_similarity=minimum_similarity,
            dataset=dataset,
            document_type=document_type,
        )
        self.build_prompt(question, results)
        generated = self.generator.generate(question, results, self.project_root)
        return ChatResult(answer=generated.text, sources=generated.sources, results=results)

    def documents(self) -> list[DocumentInfo]:
        return self.store.load().documents

    @staticmethod
    def build_prompt(question: str, results: list[SearchResult]) -> str:
        context = "\n\n".join(
            f"[{index}] Source: {result.chunk.metadata.source}\n"
            f"Section: {result.chunk.metadata.section_title}\n{result.chunk.content}"
            for index, result in enumerate(results, start=1)
        )
        return PROMPT_TEMPLATE.format(question=question, context=context)
