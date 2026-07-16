import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings


def test_system_info(client: TestClient) -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    body = response.json()
    assert body["backend"]["status"] == "operational"
    assert body["database"]["status"] == "connected"
    assert body["modules"]["data_intelligence"] == "preparation_ready"
    assert body["modules"]["forecasting"] == "next"
    assert set(value for key, value in body["modules"].items() if key not in {"data_intelligence", "forecasting"}) == {
        "planned"
    }


def test_production_rejects_debug() -> None:
    with pytest.raises(ValidationError, match="DEBUG must be false"):
        Settings(app_env="production", debug=True)


def test_production_debug_defaults_off() -> None:
    assert Settings(app_env="production", debug=False).debug is False
