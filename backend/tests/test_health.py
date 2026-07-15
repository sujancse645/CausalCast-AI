from datetime import datetime

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == "0.1.0"


def test_health_schema_and_timestamp(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "causalcast-backend"
    assert datetime.fromisoformat(body["timestamp"])


def test_unknown_route(client: TestClient) -> None:
    assert client.get("/missing").status_code == 404
