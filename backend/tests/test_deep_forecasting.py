from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.deep_forecasting import DeepForecastDataConfig, DeepForecastRuntimeConfig
from app.services.deep_forecasting.data_pipeline import _series_id, resolve_input_size
from app.services.deep_forecasting.errors import DeepArtifactStorageError, DeepHardwareConfigurationError
from app.services.deep_forecasting.hardware_service import _detect, hardware_report
from app.services.deep_forecasting.storage import DeepForecastStorage
from tests.test_preparations import config, ready_dataset


def test_deep_capabilities_and_registry_are_truthful(client) -> None:
    capability = client.get("/api/v1/forecasting/deep/capabilities")
    assert capability.status_code == 200
    body = capability.json()
    assert body["training_status"] == "nhits_training_ready"
    assert body["hardware"]["selected_accelerator"] in {"cpu", "cuda", "mps"}
    models = client.get("/api/v1/forecasting/deep/models").json()
    statuses = {item["identifier"]: item["implementation_status"] for item in models}
    assert statuses["nhits"] == "training_ready"
    assert statuses["temporal_fusion_transformer"] == statuses["nbeats"] == "planned"
    assert all(item["implementation_status"] != "production_ready" for item in models)


def test_dependency_and_hardware_endpoints_do_not_require_torch(client) -> None:
    dependencies = client.get("/api/v1/forecasting/deep/dependencies")
    assert dependencies.status_code == 200
    torch = next(item for item in dependencies.json() if item["package_name"] == "torch")
    assert isinstance(torch["installed"], bool)
    assert "import_error_category" in torch
    hardware = client.get("/api/v1/forecasting/deep/hardware")
    assert hardware.status_code == 200
    assert hardware.json()["cpu_fallback_enabled"] is True


def test_invalid_cuda_request_without_fallback_fails_safely() -> None:
    _detect.cache_clear()
    if hardware_report(Settings()).cuda_available:
        pytest.skip("CUDA is available on this host")
    settings = Settings(deep_forecasting_accelerator="cuda", deep_forecasting_cpu_fallback=False)
    with pytest.raises(DeepHardwareConfigurationError):
        hardware_report(settings)


def test_deep_configuration_validation_and_window_resolution() -> None:
    with pytest.raises(ValidationError):
        DeepForecastRuntimeConfig(devices=0)
    with pytest.raises(ValidationError):
        DeepForecastDataConfig(
            target_column="revenue",
            time_column="date",
            group_columns=["channel"],
            frequency="daily",
            forecast_horizon=30,
            input_size=120,
            historical_covariates=["revenue"],
        )
    assert resolve_input_size(30, 500, Settings(), None) == 120


def test_composite_series_ids_are_deterministic_and_unambiguous() -> None:
    assert _series_id(("a|b", "c")) == _series_id(("a|b", "c"))
    assert _series_id(("a|b", "c")) != _series_id(("a", "b|c"))


def test_deep_storage_is_atomic_checksummed_and_blocks_traversal(tmp_path: Path) -> None:
    settings = Settings(forecast_artifact_root=tmp_path)
    storage = DeepForecastStorage(settings)
    prepared = "00000000-0000-4000-8000-000000000001"
    snapshot = "00000000-0000-4000-8000-000000000002"
    manifest = storage.write_json(prepared, snapshot, "readiness_report", {"synthetic_data": True})
    assert len(str(manifest["checksum"])) == 64
    assert not Path(str(manifest["storage_key"])).is_absolute()
    with pytest.raises(DeepArtifactStorageError):
        storage.resolve("../../secret.txt")


def test_readiness_endpoint_analyzes_without_training_or_checkpoint(client) -> None:
    dataset_id, _ = ready_dataset(client)
    prepared = client.post(f"/api/v1/datasets/{dataset_id}/preparations", json=config())
    assert prepared.status_code == 201
    prepared_id = prepared.json()["id"]
    response = client.post(
        f"/api/v1/preparations/{prepared_id}/deep-readiness",
        json={
            "model_name": "nhits",
            "horizon": 2,
            "input_size": 28,
            "scaler_type": "robust",
            "scale_per_series": True,
            "target_transform": "none",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["training_executed"] is False
    assert body["checkpoint_created"] is False
    assert body["series_count"] >= 1
    assert body["artifact_checksums"]["readiness_report"]
    assert client.get(f"/api/v1/preparations/{prepared_id}/deep-readiness").status_code == 200
