from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    source: str
    section_title: str
    dataset_name: str | None
    document_type: str
    timestamp: str
    checksum: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DocumentMetadata:
        return cls(**value)


@dataclass(frozen=True, slots=True)
class SourceDocument:
    content: str
    metadata: DocumentMetadata


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    id: str
    content: str
    start_character: int
    end_character: int
    metadata: DocumentMetadata

    @property
    def embedding_text(self) -> str:
        dataset = f"Dataset: {self.metadata.dataset_name}\n" if self.metadata.dataset_name else ""
        return f"Source: {self.metadata.source}\nSection: {self.metadata.section_title}\n{dataset}{self.content}"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["metadata"] = self.metadata.to_dict()
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> DocumentChunk:
        payload = dict(value)
        payload["metadata"] = DocumentMetadata.from_dict(payload["metadata"])
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class DocumentInfo:
    source: str
    dataset_name: str | None
    document_type: str
    timestamp: str
    checksum: str
    chunk_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk: DocumentChunk
    similarity: float
