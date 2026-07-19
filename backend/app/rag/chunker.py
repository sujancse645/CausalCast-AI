from __future__ import annotations

import hashlib
import re

from app.rag.metadata import DocumentChunk, SourceDocument


class SemanticChunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 150) -> None:
        if chunk_size < 200:
            raise ValueError("Chunk size must be at least 200 characters")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("Overlap must be non-negative and smaller than chunk size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: list[SourceDocument]) -> list[DocumentChunk]:
        return [chunk for document in documents for chunk in self.chunk(document)]

    def chunk(self, document: SourceDocument) -> list[DocumentChunk]:
        text = re.sub(r"[ \t]+", " ", document.content.replace("\r\n", "\n")).strip()
        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(text):
            maximum = min(start + self.chunk_size, len(text))
            end = self._semantic_boundary(text, start, maximum)
            content = text[start:end].strip()
            if content:
                identifier = hashlib.sha256(
                    f"{document.metadata.source}|{document.metadata.section_title}|{start}|{end}|{content}".encode()
                ).hexdigest()
                chunks.append(
                    DocumentChunk(
                        id=identifier,
                        content=content,
                        start_character=start,
                        end_character=end,
                        metadata=document.metadata,
                    )
                )
            if end >= len(text):
                break
            start = max(end - self.overlap, start + 1)
        return chunks

    @staticmethod
    def _semantic_boundary(text: str, start: int, maximum: int) -> int:
        if maximum >= len(text):
            return len(text)
        minimum = start + int((maximum - start) * 0.6)
        window = text[minimum:maximum]
        for separator in ("\n\n", "\n", ". ", "; ", ", "):
            location = window.rfind(separator)
            if location >= 0:
                return minimum + location + len(separator)
        return maximum
