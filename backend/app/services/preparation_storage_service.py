import csv
import hashlib
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from app.core.config import Settings


class PreparationStorageService:
    def __init__(self, settings: Settings) -> None:
        self.root = (settings.preparation_storage_root / "prepared").resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def write(
        self, preparation_id: str, columns: list[str], rows: list[dict[str, Any]], manifests: dict[str, object]
    ) -> tuple[str, str]:
        uuid.UUID(preparation_id)
        final = (self.root / preparation_id).resolve()
        temporary = (self.root / f".{preparation_id}.tmp").resolve()
        self._assert_directory(final)
        self._assert_directory(temporary)
        shutil.rmtree(temporary, ignore_errors=True)
        temporary.mkdir()
        try:
            artifact = temporary / "prepared.csv"
            digest = hashlib.sha256()
            with artifact.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
            with artifact.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
            for name, payload in manifests.items():
                (temporary / f"{name}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
            if final.exists():
                raise OSError("Preparation artifact already exists")
            temporary.replace(final)
            return f"prepared/{preparation_id}/prepared.csv", digest.hexdigest()
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def artifact(self, preparation_id: str) -> Path:
        uuid.UUID(preparation_id)
        path = (self.root / preparation_id / "prepared.csv").resolve()
        if self.root not in path.parents or not path.is_file():
            raise FileNotFoundError("Prepared artifact unavailable")
        return path

    def json_file(self, preparation_id: str, name: str) -> object:
        if name not in {"preview", "splits", "feature_catalog", "manifest", "preparation_report"}:
            raise ValueError("Unsupported manifest")
        path = self.artifact(preparation_id).parent / f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def cleanup(self, preparation_id: str) -> None:
        uuid.UUID(preparation_id)
        path = (self.root / preparation_id).resolve()
        self._assert_directory(path)
        shutil.rmtree(path, ignore_errors=True)

    def _assert_directory(self, path: Path) -> None:
        if path.parent != self.root:
            raise ValueError("Invalid preparation storage path")
