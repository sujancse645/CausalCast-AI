import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.models.schema_profile import PhysicalType
from app.services.column_profiler import normalize_column_name, profile_values

FIXTURES = Path(__file__).parent / "fixtures"


def upload_fixture(client: TestClient, name: str) -> str:
    content = (FIXTURES / name).read_bytes()
    response = client.post("/api/v1/datasets/upload", files={"file": (name, io.BytesIO(content), "text/csv")})
    assert response.status_code == 201
    return str(response.json()["id"])


def infer(client: TestClient, dataset_id: str):
    return client.post(f"/api/v1/datasets/{dataset_id}/schema/infer", json={"reason": "test"})


@pytest.mark.parametrize(
    ("name", "values", "expected"),
    [
        ("count", ["1", "2", "3"], PhysicalType.integer),
        ("amount", ["1.2", "2.5"], PhysicalType.float),
        ("flag", ["true", "false"], PhysicalType.boolean),
        ("date", ["2026-01-01", "2026-01-02"], PhysicalType.date),
        ("timestamp", ["2026-01-01 10:00:00", "2026-01-02 11:00:00"], PhysicalType.datetime),
        ("channel", ["A", "A", "B", "B"], PhysicalType.categorical),
        ("customer_id", ["A1", "A2", "A3"], PhysicalType.identifier),
        ("mixed", ["1", "alpha", "2"], PhysicalType.mixed),
    ],
)
def test_physical_types(name: list[str] | str, values: list[str], expected: PhysicalType) -> None:
    assert profile_values(0, str(name), values, 10, 100).physical_type == expected


def test_name_normalization() -> None:
    assert normalize_column_name(" Total Revenue ") == "total_revenue"
    assert normalize_column_name("adSpend") == "ad_spend"
    assert normalize_column_name("Conv.") == "conv"


def test_canonical_inference_roles_evidence_and_bounds(client: TestClient) -> None:
    dataset_id = upload_fixture(client, "canonical_marketing.csv")
    response = infer(client, dataset_id)
    assert response.status_code == 201
    body = response.json()
    roles = {c["column_name"]: c["semantic_role"] for c in body["columns"]}
    assert roles == {
        "date": "date",
        "channel": "channel",
        "campaign": "campaign",
        "impressions": "impressions",
        "clicks": "clicks",
        "spend": "spend",
        "conversions": "conversions",
        "revenue": "revenue",
    }
    for column in body["columns"]:
        assert 0 <= column["confidence_score"] <= 1
        assert column["evidence"]
        assert column["alternatives"]
        assert len(column["sample_values"]) <= 10
    assert body["summary"]["readiness_status"] == "mapping_ready"
    assert "storage_key" not in str(body)


def test_exact_compatible_is_high_and_incompatible_is_lower(client: TestClient) -> None:
    dataset_id = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("bad.csv", io.BytesIO(b"date,revenue\n2026-01-01,uuid-a\n2026-01-02,uuid-b\n"), "text/csv")},
    ).json()["id"]
    body = infer(client, dataset_id).json()
    revenue = next(c for c in body["columns"] if c["column_name"] == "revenue")
    assert revenue["confidence_score"] < 0.6 and revenue["semantic_role"] == "unknown"


def test_ambiguous_generic_name_has_alternatives(client: TestClient) -> None:
    body = infer(client, upload_fixture(client, "ambiguous_columns.csv")).json()
    value = next(c for c in body["columns"] if c["column_name"] == "value")
    assert value["semantic_role"] == "unknown"
    assert len(value["alternatives"]) == 3
    assert value["warnings"]


def test_relationship_evidence_and_zero_division(client: TestClient) -> None:
    body = infer(client, upload_fixture(client, "ratio_metrics.csv")).json()
    for role in ("roas", "ctr", "cpc", "cpa"):
        column = next(c for c in body["columns"] if c["semantic_role"] == role)
        assert any(e["evidence_type"] == "relationship" for e in column["evidence"])


def test_determinism_versions_history_and_active(client: TestClient) -> None:
    dataset_id = upload_fixture(client, "canonical_marketing.csv")
    first = infer(client, dataset_id).json()
    second = infer(client, dataset_id).json()
    assert [(c["semantic_role"], c["confidence_score"]) for c in first["columns"]] == [
        (c["semantic_role"], c["confidence_score"]) for c in second["columns"]
    ]
    assert second["schema_version"] == 2
    history = client.get(f"/api/v1/datasets/{dataset_id}/schema/history").json()["items"]
    assert len(history) == 2
    assert client.get(f"/api/v1/datasets/{dataset_id}/schema").json()["schema_version"] == 2


def test_override_invalid_role_and_confirmation(client: TestClient) -> None:
    dataset_id = upload_fixture(client, "ambiguous_columns.csv")
    schema = infer(client, dataset_id).json()
    value = next(c for c in schema["columns"] if c["column_name"] == "value")
    notes = next(c for c in schema["columns"] if c["column_name"] == "notes")
    assert client.post(f"/api/v1/datasets/{dataset_id}/schema/confirm", json={}).status_code == 422
    assert (
        client.patch(
            f"/api/v1/datasets/{dataset_id}/schema/columns/{value['id']}", json={"semantic_role": "not_real"}
        ).status_code
        == 422
    )
    updated = client.patch(
        f"/api/v1/datasets/{dataset_id}/schema/columns/{value['id']}",
        json={"semantic_role": "revenue", "reason": "local review"},
    ).json()["column"]
    assert updated["decision_source"] == "user_override" and updated["confirmation_status"] == "manually_overridden"
    client.patch(f"/api/v1/datasets/{dataset_id}/schema/columns/{notes['id']}", json={"semantic_role": "ignored"})
    confirmed = client.post(f"/api/v1/datasets/{dataset_id}/schema/confirm", json={})
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"


def test_missing_date_warning_and_schema_stats(client: TestClient) -> None:
    dataset_id = client.post(
        "/api/v1/datasets/upload", files={"file": ("nodate.csv", io.BytesIO(b"revenue,spend\n100,20\n"), "text/csv")}
    ).json()["id"]
    body = infer(client, dataset_id).json()
    assert any(x["code"] == "missing_date" for x in body["summary"]["blocking_issues"])
    assert client.get("/api/v1/datasets/schema/stats").json()["awaiting_review"] >= 1


def test_missing_archived_and_missing_file_errors(client: TestClient) -> None:
    assert infer(client, "00000000-0000-4000-8000-000000000000").status_code == 404
    archived = upload_fixture(client, "canonical_marketing.csv")
    client.delete(f"/api/v1/datasets/{archived}")
    assert infer(client, archived).status_code == 409
    missing = upload_fixture(client, "ambiguous_columns.csv")
    from app.core.config import get_settings

    next((get_settings().dataset_storage_root / "uploads").glob(f"{missing}.csv")).unlink()
    assert infer(client, missing).status_code == 409


def test_roles_list_library_status_and_openapi(client: TestClient) -> None:
    roles = client.get("/api/v1/schema/roles")
    assert roles.status_code == 200
    assert any(x["role"] == "revenue" for x in roles.json()["items"])
    dataset_id = upload_fixture(client, "canonical_marketing.csv")
    assert client.get("/api/v1/datasets").json()["items"][0]["schema_status"] == "not_analyzed"
    infer(client, dataset_id)
    assert client.get("/api/v1/datasets").json()["items"][0]["schema_status"] == "needs_review"
    assert "/api/v1/datasets/{dataset_id}/schema/infer" in client.get("/openapi.json").json()["paths"]
