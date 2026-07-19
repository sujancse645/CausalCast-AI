from __future__ import annotations

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.rag.document_registry import DocumentRegistry, RegistryEntry
from app.rag.metadata import DocumentMetadata, SourceDocument

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


class ProjectDocumentLoader:
    def __init__(self, registry: DocumentRegistry, max_csv_rows: int = 20_000) -> None:
        self.registry = registry
        self.max_csv_rows = max_csv_rows

    def load_all(self) -> list[SourceDocument]:
        documents: list[SourceDocument] = []
        for entry in self.registry.entries():
            documents.extend(self.load(entry))
        return documents

    def load(self, entry: RegistryEntry) -> list[SourceDocument]:
        timestamp = datetime.fromtimestamp(entry.path.stat().st_mtime, tz=UTC).isoformat()
        if entry.document_type == "markdown":
            sections = self._markdown(entry.path)
        elif entry.document_type == "json":
            sections = self._json(entry.path)
        elif entry.document_type == "csv":
            sections = self._csv(entry.path)
        else:
            sections = [(entry.path.stem, self._read_text(entry.path))]
        return [
            SourceDocument(
                content=content,
                metadata=DocumentMetadata(
                    source=entry.source,
                    section_title=title,
                    dataset_name=entry.dataset_name,
                    document_type=entry.document_type,
                    timestamp=timestamp,
                    checksum=entry.checksum,
                ),
            )
            for title, content in sections
            if content.strip()
        ]

    @staticmethod
    def _read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8-sig", errors="replace").replace("\x00", "")

    def _markdown(self, path: Path) -> list[tuple[str, str]]:
        text = self._read_text(path)
        title = path.stem.replace("-", " ").replace("_", " ").title()
        sections: list[tuple[str, str]] = []
        buffer: list[str] = []
        current = title
        for line in text.splitlines():
            match = HEADING.match(line)
            if match:
                if "\n".join(buffer).strip():
                    sections.append((current, "\n".join(buffer).strip()))
                current = match.group(2).strip()
                buffer = [line]
            else:
                buffer.append(line)
        if "\n".join(buffer).strip():
            sections.append((current, "\n".join(buffer).strip()))
        return sections

    def _json(self, path: Path) -> list[tuple[str, str]]:
        value: Any = json.loads(self._read_text(path))
        if isinstance(value, list) and value:
            return [
                (
                    f"{path.stem} records {start + 1}-{min(start + 25, len(value))}",
                    json.dumps(value[start : start + 25], indent=2, ensure_ascii=False),
                )
                for start in range(0, len(value), 25)
            ]
        return [(path.stem.replace("_", " ").title(), json.dumps(value, indent=2, ensure_ascii=False))]

    def _csv(self, path: Path) -> list[tuple[str, str]]:
        sections: list[tuple[str, str]] = []
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = [str(field) for field in (reader.fieldnames or [])]
            if not fields:
                return []
            rows: list[str] = []
            start = 1
            for row_number, row in enumerate(reader, start=1):
                if row_number > self.max_csv_rows:
                    break
                rendered = ", ".join(f"{field}={str(row.get(field, ''))[:1000]}" for field in fields)
                rows.append(rendered)
                if len(rows) == 50:
                    content = "Columns: " + ", ".join(fields) + "\n" + "\n".join(rows)
                    sections.append((f"{path.stem} rows {start}-{row_number}", content))
                    start = row_number + 1
                    rows = []
            if rows:
                end = start + len(rows) - 1
                content = "Columns: " + ", ".join(fields) + "\n" + "\n".join(rows)
                sections.append((f"{path.stem} rows {start}-{end}", content))
        return sections
