from pathlib import Path
from typing import Any


class CheckpointService:
    """Validates application-owned NeuralForecast checkpoint directories."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def resolve(self, storage_key: str) -> Path:
        if Path(storage_key).is_absolute():
            raise ValueError("Absolute checkpoint paths are not accepted")
        path = (self.root / storage_key).resolve()
        if self.root not in path.parents or not path.is_dir() or path.is_symlink():
            raise FileNotFoundError("Checkpoint is unavailable")
        return path

    def load(self, storage_key: str) -> Any:
        from neuralforecast import NeuralForecast

        return NeuralForecast.load(str(self.resolve(storage_key)))
