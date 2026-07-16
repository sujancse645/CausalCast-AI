from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES = Path(__file__).parent / "fixtures"


def prepare(client: TestClient, name: str) -> str:
    with (FIXTURES / name).open("rb") as stream:
        upload = client.post("/api/v1/datasets/upload", files={"file": (name, stream, "text/csv")})
    assert upload.status_code == 201, upload.text
    dataset_id = upload.json()["id"]
    inferred = client.post(f"/api/v1/datasets/{dataset_id}/schema/infer", json={"force_reinfer": True})
    assert inferred.status_code == 201, inferred.text
    expected = {
        "date": "date",
        "channel": "channel",
        "campaign": "campaign",
        "impressions": "impressions",
        "clicks": "clicks",
        "spend": "spend",
        "conversions": "conversions",
        "revenue": "revenue",
        "roas": "roas",
        "ctr": "ctr",
    }
    for column in inferred.json()["columns"]:
        if column["column_name"] in expected and column["semantic_role"] != expected[column["column_name"]]:
            changed = client.patch(
                f"/api/v1/datasets/{dataset_id}/schema/columns/{column['id']}",
                json={"semantic_role": expected[column["column_name"]], "reason": "deterministic test review"},
            )
            assert changed.status_code == 200, changed.text
    return dataset_id


def analyze(client: TestClient, name: str) -> dict[str, object]:
    dataset_id = prepare(client, name)
    response = client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={"force_reanalyze": True})
    assert response.status_code == 201, response.text
    return response.json()


def codes(report: dict[str, object]) -> set[str]:
    return {item["rule_code"] for item in report["findings"]}  # type: ignore[index, union-attr]


def test_quality_analysis_persists_versions_and_history(client: TestClient) -> None:
    dataset_id = prepare(client, "quality_clean.csv")
    first = client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={}).json()
    second = client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={}).json()
    assert first["report_version"] == 1 and second["report_version"] == 2
    history = client.get(f"/api/v1/datasets/{dataset_id}/quality/history").json()["items"]
    assert len(history) == 2 and history[1]["status"] == "superseded"
    assert client.get(f"/api/v1/datasets/{dataset_id}/quality").status_code == 200


def test_missingness_empty_tokens_zero_and_scores(client: TestClient) -> None:
    report = analyze(client, "quality_missing.csv")
    missing = [f for f in report["findings"] if f["rule_code"] == "DQ_COMPLETENESS_001"]
    assert any(f["affected_column"] == "revenue" and f["affected_row_count"] == 1 for f in missing)
    assert any(f["affected_column"] == "channel" and f["affected_row_count"] == 2 for f in missing)
    assert all(0 <= value <= 100 for value in report["dimension_scores"].values())


def test_duplicates_and_business_key(client: TestClient) -> None:
    report = analyze(client, "quality_duplicates.csv")
    assert {"DQ_DUPLICATE_001", "DQ_DUPLICATE_002"}.issubset(codes(report))
    duplicate = next(f for f in report["findings"] if f["rule_code"] == "DQ_DUPLICATE_001")
    assert duplicate["affected_row_count"] == 1
    assert len(duplicate["sample_row_indices"]) <= 10


def test_invalid_types_dates_and_negative_counts(client: TestClient) -> None:
    report = analyze(client, "quality_invalid_types.csv")
    assert {"DQ_VALIDITY_001", "DQ_VALIDITY_002", "DQ_TEMPORAL_001"}.issubset(codes(report))


def test_iqr_outlier_is_explainable(client: TestClient) -> None:
    report = analyze(client, "quality_outliers.csv")
    finding = next(f for f in report["findings"] if f["rule_code"] == "DQ_OUTLIER_001")
    assert finding["evidence"]["method"] == "IQR"
    assert finding["severity"] in {"warning", "error"}


def test_temporal_gaps_order_and_frequency(client: TestClient) -> None:
    report = analyze(client, "quality_temporal_gaps.csv")
    assert {"DQ_TEMPORAL_002", "DQ_TEMPORAL_003"}.issubset(codes(report))
    assert report["summary"]["temporal"]["frequency"] == "daily"


def test_relationships_and_zero_division_are_safe(client: TestClient) -> None:
    report = analyze(client, "quality_relationship_errors.csv")
    assert {"DQ_RELATIONSHIP_001", "DQ_RELATIONSHIP_002"}.issubset(codes(report))


def test_leakage_copy_future_name_and_derived_metric_block(client: TestClient) -> None:
    report = analyze(client, "quality_leakage.csv")
    assert {"DQ_LEAKAGE_001", "DQ_LEAKAGE_002", "DQ_LEAKAGE_003"}.issubset(codes(report))
    assert report["readiness_status"] == "blocked"
    assert report["overall_score"] <= 49


def test_constants_high_cardinality_and_percentages(client: TestClient) -> None:
    constant = analyze(client, "quality_constant_columns.csv")
    assert "DQ_CARDINALITY_001" in codes(constant)
    high = analyze(client, "quality_high_cardinality.csv")
    assert "DQ_CARDINALITY_002" in codes(high)
    percentage = analyze(client, "quality_mixed_percentages.csv")
    assert "DQ_VALIDITY_003" in codes(percentage)


def test_missing_schema_archived_and_unknown_report_errors(client: TestClient) -> None:
    with (FIXTURES / "quality_clean.csv").open("rb") as stream:
        dataset_id = client.post("/api/v1/datasets/upload", files={"file": ("new.csv", stream, "text/csv")}).json()[
            "id"
        ]
    assert client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={}).status_code == 422
    assert client.get(f"/api/v1/datasets/{dataset_id}/quality").status_code == 404
    assert client.delete(f"/api/v1/datasets/{dataset_id}").status_code == 200
    assert client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={}).status_code == 409


def test_findings_filter_pagination_rules_stats_and_no_paths(client: TestClient) -> None:
    report = analyze(client, "quality_leakage.csv")
    dataset_id = report["dataset_id"]
    filtered = client.get(f"/api/v1/datasets/{dataset_id}/quality/findings?category=leakage&blocking=true&page_size=1")
    assert filtered.status_code == 200
    assert filtered.json()["pagination"]["page_size"] == 1
    assert all(item["blocking"] for item in filtered.json()["items"])
    assert client.get("/api/v1/quality/rules").json()["items"]
    assert client.get("/api/v1/datasets/quality/stats").status_code == 200
    serialized = str(report).lower()
    assert "storage_key" not in serialized and "stored_filename" not in serialized
    assert client.get("/openapi.json").status_code == 200


def test_scores_are_deterministic(client: TestClient) -> None:
    dataset_id = prepare(client, "quality_relationship_errors.csv")
    one = client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={}).json()
    two = client.post(f"/api/v1/datasets/{dataset_id}/quality/analyze", json={}).json()
    assert one["overall_score"] == two["overall_score"]
    assert one["dimension_scores"] == two["dimension_scores"]
