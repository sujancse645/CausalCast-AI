from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class NHiTSConfig(BaseModel):
    """Validated, serializable N-HiTS training configuration."""

    forecast_horizon: int = Field(default=30, ge=1, le=365)
    input_size: int = Field(default=120, ge=1, le=365)
    learning_rate: float = Field(default=1e-3, gt=0, le=1)
    batch_size: int = Field(default=32, ge=1, le=4096)
    windows_batch_size: int = Field(default=1024, ge=1, le=65536)
    max_steps: int = Field(default=1000, ge=1, le=1_000_000)
    dropout: float = Field(default=0.0, ge=0, lt=1)
    hidden_size: int = Field(default=512, ge=4, le=8192)
    hidden_layers: int = Field(default=2, ge=1, le=8)
    stack_count: int = Field(default=3, ge=1, le=8)
    blocks_per_stack: int = Field(default=1, ge=1, le=8)
    activation: Literal["ReLU", "Softplus", "Tanh", "SELU", "LeakyReLU", "PReLU", "Sigmoid"] = "ReLU"
    optimizer: Literal["adam", "adamw", "sgd"] = "adam"
    scheduler: Literal["none", "step", "cosine"] = "none"
    weight_decay: float = Field(default=0.0, ge=0, le=1)
    early_stopping_patience_steps: int = Field(default=-1, ge=-1, le=100_000)
    validation_check_steps: int = Field(default=100, ge=1, le=100_000)
    scaler_type: Literal["identity", "standard", "robust", "minmax"] = "robust"
    random_seed: int = Field(default=42, ge=0, le=2**32 - 1)
    accelerator: Literal["auto", "cpu", "cuda", "mps"] = "auto"
    devices: int = Field(default=1, ge=1, le=64)
    deterministic: bool = True
    checkpoint_every_n_steps: int = Field(default=100, ge=1, le=100_000)

    @model_validator(mode="after")
    def validate_windows(self) -> "NHiTSConfig":
        if self.input_size < self.forecast_horizon:
            raise ValueError("input_size must be at least forecast_horizon")
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> "NHiTSConfig":
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("N-HiTS YAML must contain an object")
        return cls.model_validate(payload)

    def to_yaml(self) -> str:
        return str(yaml.safe_dump(self.model_dump(mode="json"), sort_keys=True))
