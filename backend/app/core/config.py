from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CausalCast AI"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "sqlite:///./causalcast.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    dataset_storage_root: Path = Path("../data/raw")
    dataset_upload_dir: str = "uploads"
    dataset_quarantine_dir: str = "quarantine"
    dataset_archive_dir: str = "archived"
    max_upload_size_mb: int = 25
    allowed_dataset_extensions: list[str] = ["csv"]
    dataset_preview_rows: int = 20
    dataset_max_columns: int = 500
    dataset_max_rows_for_preview_scan: int = 10000
    dataset_ingestion_version: int = 1
    dataset_delete_mode: Literal["archive"] = "archive"
    dataset_max_cell_length: int = 500

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @field_validator("cors_origins", "allowed_dataset_extensions", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("max_upload_size_mb", "dataset_preview_rows", "dataset_max_columns")
    @classmethod
    def positive_limits(cls, value: int) -> int:
        if value < 1:
            raise ValueError("Dataset limits must be positive")
        return value

    @model_validator(mode="after")
    def secure_production_defaults(self) -> "Settings":
        if self.app_env == "production" and self.debug:
            raise ValueError("DEBUG must be false in production")
        if "*" in self.cors_origins:
            raise ValueError("Wildcard CORS origins are not permitted")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
