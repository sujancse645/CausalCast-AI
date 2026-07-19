import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services.production_forecast_service import ASSETS, ProductionForecastService


def _assets_available() -> bool:
    root = get_settings().project_root
    return all(
        (root / item.model_relative).is_file() and (root / item.data_relative).is_file() for item in ASSETS.values()
    )


@pytest.mark.skipif(not _assets_available(), reason="External trained model and data assets are not installed")
def test_real_forecast_asset_registry_and_online_retail_prediction() -> None:
    service = ProductionForecastService(get_settings())
    datasets = service.datasets()
    assert {item.id for item in datasets} == {"rossmann", "electricity", "m4_daily", "online_retail", "tourism"}
    assert all(item.model_available and item.data_available for item in datasets)

    result = service.forecast("online_retail", horizon=3)
    assert result.prediction_kind == "held_out_test"
    assert result.model_loaded_from_disk is True
    assert result.rows_used == 3
    assert len(result.predictions) == 3
    assert all(point.prediction >= 0 and point.actual is not None for point in result.predictions)


@pytest.mark.skipif(not _assets_available(), reason="External trained model and data assets are not installed")
def test_production_forecast_api_uses_authenticated_real_assets(client: TestClient) -> None:
    response = client.post("/api/v1/forecast", json={"dataset": "tourism", "horizon": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["dataset"] == "tourism"
    assert body["prediction_kind"] == "held_out_test"
    assert len(body["predictions"]) == 2
    assert body["model_checksum"]

    metadata = client.get("/api/v1/forecast-datasets/tourism/metadata")
    assert metadata.status_code == 200
    assert metadata.json()["frequency"] == "yearly"
