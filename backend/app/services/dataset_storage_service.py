import hashlib
import logging
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import DatasetStorageError, DatasetTooLargeError, InvalidDatasetError

logger = logging.getLogger(__name__)
CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class StoredUpload:
    dataset_id: str
    original_filename: str
    stored_filename: str
    storage_key: str
    path: Path
    size: int
    checksum: str


class DatasetStorageService:
    def __init__(self, settings: Settings) -> None:
        self.root = settings.dataset_storage_root.resolve()
        self.upload_dir = self._safe_directory(settings.dataset_upload_dir)
        self.quarantine_dir = self._safe_directory(settings.dataset_quarantine_dir)
        self.archive_dir = self._safe_directory(settings.dataset_archive_dir)
        self.max_bytes = settings.max_upload_size_mb * 1024 * 1024
        for directory in (self.upload_dir, self.quarantine_dir, self.archive_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def _safe_directory(self, name: str) -> Path:
        candidate = (self.root / name).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise DatasetStorageError("Invalid storage configuration")
        return candidate

    @staticmethod
    def normalize_filename(filename: str | None) -> str:
        raw = Path((filename or "dataset.csv").replace("\\", "/")).name
        safe = re.sub(r"[^A-Za-z0-9._ -]", "_", raw).strip(" .")
        return safe[:255] or "dataset.csv"

    async def save(self, upload: UploadFile, extension: str) -> StoredUpload:
        dataset_id = str(uuid.uuid4())
        stored_filename = f"{dataset_id}.{extension}"
        final_path = (self.upload_dir / stored_filename).resolve()
        temporary_path = (self.upload_dir / f".{dataset_id}.part").resolve()
        self._assert_contained(final_path, self.upload_dir)
        digest = hashlib.sha256()
        size = 0
        try:
            with temporary_path.open("xb") as target:
                while chunk := await upload.read(CHUNK_SIZE):
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise DatasetTooLargeError("Dataset exceeds the configured upload limit")
                    digest.update(chunk)
                    target.write(chunk)
            if size == 0:
                raise InvalidDatasetError("Dataset file is empty")
            temporary_path.replace(final_path)
        except (DatasetTooLargeError, InvalidDatasetError):
            temporary_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise DatasetStorageError("Dataset could not be stored") from exc
        finally:
            await upload.close()
        return StoredUpload(
            dataset_id=dataset_id,
            original_filename=self.normalize_filename(upload.filename),
            stored_filename=stored_filename,
            storage_key=f"uploads/{stored_filename}",
            path=final_path,
            size=size,
            checksum=digest.hexdigest(),
        )

    def archive(self, stored_filename: str) -> str:
        source = (self.upload_dir / stored_filename).resolve()
        target = (self.archive_dir / stored_filename).resolve()
        self._assert_contained(source, self.upload_dir)
        self._assert_contained(target, self.archive_dir)
        if not source.is_file():
            raise DatasetStorageError("Dataset file is unavailable")
        source.replace(target)
        return f"archived/{stored_filename}"

    def restore_archived(self, stored_filename: str) -> None:
        archived = (self.archive_dir / stored_filename).resolve()
        active = (self.upload_dir / stored_filename).resolve()
        self._assert_contained(archived, self.archive_dir)
        self._assert_contained(active, self.upload_dir)
        if archived.is_file():
            archived.replace(active)

    def cleanup(self, path: Path) -> None:
        self._assert_contained(path.resolve(), self.upload_dir)
        path.unlink(missing_ok=True)
        logger.info("dataset_cleanup_completed")

    @staticmethod
    def _assert_contained(path: Path, parent: Path) -> None:
        if path.parent != parent:
            raise DatasetStorageError("Invalid storage path")
