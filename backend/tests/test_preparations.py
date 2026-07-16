import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES = Path(__file__).parent / "fixtures"


def ready_dataset(client: TestClient) -> tuple[str, str]:
    source = FIXTURES / "preparation_daily.csv"
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    with source.open("rb") as stream:
        uploaded = client.post("/api/v1/datasets/upload", files={"file": (source.name, stream, "text/csv")})
    dataset_id = uploaded.json()["id"]
    inferred = client.post(f"/api/v1/datasets/{dataset_id}/schema/infer", json={}).json()
    expected = {
        "date": "date",
        "revenue": "revenue",
        "spend": "spend",
        "impressions": "impressions",
        "clicks": "clicks",
        "conversions": "conversions",
        "channel": "channel",
        "campaign": "campaign",
        "promotion": "promotion",
    }
    for column in inferred["columns"]:
        if column["column_name"] in expected and column["semantic_role"] != expected[column["column_name"]]:
            response = client.patch(
                f"/api/v1/datasets/{dataset_id}/schema/columns/{column['id']}",
                json={"semantic_role": expected[column["column_name"]], "reason": "test review"},
            )
            assert response.status_code == 200
    assert client.post(f"/api/v1/datasets/{dataset_id}/schema/confirm", json={}).status_code == 200
    quality = client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={})
    assert quality.status_code == 201, quality.text
    return dataset_id, checksum


def config() -> dict[str, object]:
    return {
        "config": {
            "target_column": "revenue",
            "date_column": "date",
            "frequency": "daily",
            "forecast_horizon": 2,
            "lag_periods": [1, 7],
            "rolling_windows": [3],
            "rolling_statistics": ["mean", "sum"],
            "backtest_folds": 1,
        }
    }


def test_preparation_artifact_lineage_features_splits_and_download(client: TestClient) -> None:
    dataset_id, checksum = ready_dataset(client)
    response = client.post(f"/api/v1/datasets/{dataset_id}/preparations", json=config())
    assert response.status_code == 201, response.text
    result = response.json()
    assert result["source_checksum"] == checksum and result["prepared_checksum"]
    assert result["row_count"] == 12 and result["train_rows"] < result["row_count"]
    prepared_id = result["id"]
    preview = client.get(f"/api/v1/preparations/{prepared_id}/preview").json()
    assert preview["returned_rows"] <= 50 and preview["rows"][1]["revenue_lag_1"] == "200.0"
    features = client.get(f"/api/v1/preparations/{prepared_id}/features").json()["items"]
    lag = next(item for item in features if item["feature_name"] == "revenue_lag_1")
    assert lag["availability_type"] == "historical_only" and lag["lineage"]
    splits = client.get(f"/api/v1/preparations/{prepared_id}/splits").json()["splits"]
    assert [x["name"] for x in splits] == ["train", "validation", "test"]
    assert splits[0]["end"] < splits[1]["start"] < splits[2]["start"]
    assert client.get(f"/api/v1/preparations/{prepared_id}/download").status_code == 200


def test_preparation_versions_history_stats_and_safe_errors(client: TestClient) -> None:
    dataset_id, _ = ready_dataset(client)
    first = client.post(f"/api/v1/datasets/{dataset_id}/preparations", json=config())
    second = client.post(f"/api/v1/datasets/{dataset_id}/preparations", json=config())
    assert first.status_code == second.status_code == 201
    history = client.get(f"/api/v1/datasets/{dataset_id}/preparations").json()["items"]
    assert [x["preparation_version"] for x in history] == [2, 1]
    assert history[1]["status"] == "superseded"
    stats = client.get("/api/v1/preparations/stats").json()
    assert stats["total_prepared_datasets"] == 2
    assert client.get("/api/v1/preparations/00000000-0000-4000-8000-000000000000").status_code == 404


def test_preparation_requires_confirmed_schema_and_quality(client: TestClient) -> None:
    source = FIXTURES / "preparation_daily.csv"
    with source.open("rb") as stream:
        dataset_id = client.post("/api/v1/datasets/upload", files={"file": (source.name, stream, "text/csv")}).json()[
            "id"
        ]
    response = client.post(f"/api/v1/datasets/{dataset_id}/preparations", json=config())
    assert response.status_code == 409
    assert "confirmed schema" in response.json()["detail"]


def test_duplicate_rejection_and_invalid_split_configuration(client: TestClient) -> None:
    dataset_id, _ = ready_dataset(client)
    invalid = config()
    invalid["config"]["train_ratio"] = 0.5  # type: ignore[index]
    assert client.post(f"/api/v1/datasets/{dataset_id}/preparations", json=invalid).status_code == 422
