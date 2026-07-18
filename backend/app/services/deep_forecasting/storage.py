import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import Settings
from app.services.deep_forecasting.errors import DeepArtifactStorageError


class DeepForecastStorage:
    ALLOWED = {
        "runtime_config",
        "data_config",
        "model_config",
        "covariate_catalog",
        "readiness_report",
        "leakage_report",
        "sequence_manifest",
        "hardware_report",
        "dependencies",
        "packages",
        "runtime",
        "artifact_manifest",
        "series_mapping",
    }

    def __init__(self, settings: Settings) -> None:
        self.root = (settings.forecast_artifact_root / "deep_forecasting").resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, prepared_id: str, snapshot_id: str) -> Path:
        uuid.UUID(prepared_id)
        uuid.UUID(snapshot_id)
        path = (self.root / "readiness" / prepared_id / snapshot_id).resolve()
        if self.root not in path.parents:
            raise DeepArtifactStorageError("Invalid deep artifact location")
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def checksum_bytes(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def write_json(self, prepared_id: str, snapshot_id: str, logical_name: str, payload: object) -> dict[str, object]:
        if logical_name not in self.ALLOWED:
            raise DeepArtifactStorageError("Unsupported deep artifact type")
        directory = self.directory(prepared_id, snapshot_id)
        content = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        final = (directory / f"{logical_name}.json").resolve()
        if directory != final.parent:
            raise DeepArtifactStorageError("Invalid deep artifact path")
        temporary = directory / f".{logical_name}.{uuid.uuid4().hex}.tmp"
        temporary.write_bytes(content)
        os.replace(temporary, final)
        return {
            "logical_name": logical_name,
            "artifact_type": "readiness",
            "storage_key": str(final.relative_to(self.root)).replace("\\", "/"),
            "checksum": self.checksum_bytes(content),
            "checksum_algorithm": "sha256",
            "size_bytes": len(content),
            "framework": "neuralforecast",
            "framework_version": None,
            "synthetic_data": bool(payload.get("synthetic_data", False)) if isinstance(payload, dict) else False,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def resolve(self, storage_key: str) -> Path:
        if Path(storage_key).is_absolute():
            raise DeepArtifactStorageError("Absolute deep artifact paths are not accepted")
        path = (self.root / storage_key).resolve()
        if self.root not in path.parents or not path.is_file() or path.is_symlink():
            raise DeepArtifactStorageError("Deep artifact is unavailable")
        return path
