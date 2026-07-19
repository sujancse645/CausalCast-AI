from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".md": "markdown", ".txt": "text", ".json": "json", ".csv": "csv"}
IGNORED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "models",
    "raw",
    "vector_db",
    "__pycache__",
}
IGNORED_SOURCES = {
    "reports/integration/rag_validation.json",
    "reports/integration/rag_validation.md",
}


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    path: Path
    source: str
    document_type: str
    dataset_name: str | None
    checksum: str
    size_bytes: int


class DocumentRegistry:
    """Allowlisted registry for project documentation and generated reports."""

    def __init__(self, project_root: Path, max_file_bytes: int = 10 * 1024 * 1024) -> None:
        self.project_root = project_root.resolve()
        self.max_file_bytes = max_file_bytes

    def entries(self) -> list[RegistryEntry]:
        candidates: list[Path] = []
        readme = self.project_root / "README.md"
        if readme.is_file():
            candidates.append(readme)
        for directory_name in ("docs", "reports"):
            directory = self.project_root / directory_name
            if directory.is_dir():
                candidates.extend(path for path in directory.rglob("*") if path.is_file())

        entries: list[RegistryEntry] = []
        for path in sorted(set(candidates), key=lambda item: item.as_posix().lower()):
            entry = self._entry(path)
            if entry is not None:
                entries.append(entry)
        return entries

    def _entry(self, path: Path) -> RegistryEntry | None:
        resolved = path.resolve()
        if self.project_root != resolved and self.project_root not in resolved.parents:
            return None
        relative = resolved.relative_to(self.project_root)
        if relative.as_posix().casefold() in IGNORED_SOURCES:
            return None
        if any(part.lower() in IGNORED_PARTS for part in relative.parts):
            return None
        document_type = SUPPORTED_SUFFIXES.get(resolved.suffix.lower())
        size = resolved.stat().st_size
        if document_type is None or size == 0 or size > self.max_file_bytes:
            return None
        dataset_name = (
            relative.parts[1]
            if relative.parts and relative.parts[0].lower() == "reports" and len(relative.parts) > 2
            else None
        )
        return RegistryEntry(
            path=resolved,
            source=relative.as_posix(),
            document_type=document_type,
            dataset_name=dataset_name,
            checksum=self._checksum(resolved),
            size_bytes=size,
        )

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while block := handle.read(1024 * 1024):
                digest.update(block)
        return digest.hexdigest()
