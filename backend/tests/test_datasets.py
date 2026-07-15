import asyncio
import io
import uuid

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.dataset_service import upload_dataset


def upload(client: TestClient, content: bytes, filename: str = "marketing.csv", mime: str = "text/csv"):
    return client.post("/api/v1/datasets/upload", files={"file": (filename, io.BytesIO(content), mime)})


@pytest.fixture(autouse=True)
def clean_datasets(client: TestClient):
    yield
    from app.core.database import SessionLocal
    from app.models.dataset import Dataset

    with SessionLocal() as db:
        db.query(Dataset).delete()
        db.commit()
    root = get_settings().dataset_storage_root
    for path in root.rglob("*") if root.exists() else []:
        if path.is_file():
            path.unlink()


def test_valid_csv_metadata_and_uuid(client: TestClient) -> None:
    response = upload(client, b"date,channel,revenue\n2026-01-01,Email,120.5\n2026-01-02,Organic,99\n")
    assert response.status_code == 201
    body = response.json()
    assert uuid.UUID(body["id"]).version == 4
    assert body["row_count"] == 2
    assert body["column_count"] == 3
    assert body["column_names"] == ["date", "channel", "revenue"]
    assert body["preview_rows"][0]["channel"] == "Email"
    assert "storage_key" not in body and "stored_filename" not in body


@pytest.mark.parametrize(
    ("content", "delimiter", "encoding"),
    [
        ("name,value\nCafé,1\n".encode(), ",", "utf-8-sig"),
        (b"\xef\xbb\xbfname,value\nCafe,1\n", ",", "utf-8-sig"),
        (b"name;value\nA;1\n", ";", "utf-8-sig"),
        (b"name\tvalue\nA\t1\n", "\t", "utf-8-sig"),
        (b'name,note\nA,"hello, world"\n', ",", "utf-8-sig"),
        (b"name,value\r\nA,1\r\n", ",", "utf-8-sig"),
    ],
)
def test_csv_variants(client: TestClient, content: bytes, delimiter: str, encoding: str) -> None:
    body = upload(client, content).json()
    assert body["delimiter"] == delimiter
    assert body["encoding"] == encoding
    assert body["row_count"] == 1


def test_preview_is_bounded(client: TestClient) -> None:
    content = "name,value\n" + "\n".join(f"row{i},{i}" for i in range(30))
    body = upload(client, content.encode()).json()
    assert len(body["preview_rows"]) == get_settings().dataset_preview_rows


def test_empty_file_rejected_and_cleaned(client: TestClient) -> None:
    assert upload(client, b"").status_code == 400
    assert not list(get_settings().dataset_storage_root.rglob("*.part"))


def test_header_only_is_ready_without_preview(client: TestClient) -> None:
    response = upload(client, b"name,value\n")
    assert response.status_code == 201
    assert response.json()["row_count"] == 0
    assert response.json()["preview_available"] is False


@pytest.mark.parametrize("filename", ["data.json", "data.csv.exe", "data..csv", "data.xls", "data.zip"])
def test_unsupported_and_double_extensions(client: TestClient, filename: str) -> None:
    assert upload(client, b"a,b\n1,2\n", filename).status_code == 415


def test_mime_mismatch_rejected(client: TestClient) -> None:
    assert upload(client, b"a,b\n1,2\n", mime="application/pdf").status_code == 415


def test_oversized_upload_rejected(client: TestClient) -> None:
    content = b"a,b\n" + b"x,y\n" * 300000
    settings = get_settings()
    original = settings.max_upload_size_mb
    settings.max_upload_size_mb = 1
    try:
        assert upload(client, content).status_code == 413
    finally:
        settings.max_upload_size_mb = original


@pytest.mark.parametrize("content", [b"a,b\n1\n", b'a,b\n"unterminated,2\n', b",\n1,2\n"])
def test_invalid_csv_safe(client: TestClient, content: bytes) -> None:
    assert upload(client, content).status_code in {400, 422}


def test_duplicate_conflict(client: TestClient) -> None:
    content = b"a,b\n1,2\n"
    first = upload(client, content)
    second = upload(client, content, "copy.csv")
    assert second.status_code == 409
    assert second.json()["existing_dataset_id"] == first.json()["id"]


def test_list_detail_preview_archive_flow(client: TestClient) -> None:
    dataset_id = upload(client, b"a,b\n1,2\n3,4\n").json()["id"]
    listing = client.get("/api/v1/datasets?page=1&page_size=1")
    assert listing.status_code == 200
    assert listing.json()["pagination"]["total_items"] == 1
    detail = client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail.status_code == 200 and "storage_key" not in detail.json()
    preview = client.get(f"/api/v1/datasets/{dataset_id}/preview?limit=1")
    assert preview.json()["returned_rows"] == 1
    archived = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert archived.status_code == 200 and archived.json()["status"] == "archived"
    assert client.get(f"/api/v1/datasets/{dataset_id}/preview").status_code == 404


def test_unknown_dataset(client: TestClient) -> None:
    unknown = str(uuid.uuid4())
    assert client.get(f"/api/v1/datasets/{unknown}").status_code == 404
    assert client.delete(f"/api/v1/datasets/{unknown}").status_code == 404


def test_path_traversal_filename_is_neutralized(client: TestClient) -> None:
    body = upload(client, b"a,b\n1,2\n", "../../escape.csv").json()
    assert body["original_filename"] == "escape.csv"
    assert not (get_settings().dataset_storage_root.parent / "escape.csv").exists()


def test_stats_use_real_records(client: TestClient) -> None:
    assert client.get("/api/v1/datasets/stats").json()["active_datasets"] == 0
    upload(client, b"a,b\n1,2\n", "stats.csv")
    stats = client.get("/api/v1/datasets/stats").json()
    assert stats["active_datasets"] == 1 and stats["latest_filename"] == "stats.csv"


def test_openapi_contains_dataset_routes(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert "/api/v1/datasets/upload" in schema["paths"]


def test_database_failure_does_not_leave_orphan(monkeypatch: pytest.MonkeyPatch) -> None:
    db = SessionLocal()
    monkeypatch.setattr(db, "commit", lambda: (_ for _ in ()).throw(SQLAlchemyError("test failure")))
    candidate = UploadFile(filename="failure.csv", file=io.BytesIO(b"a,b\n1,2\n"), headers={"content-type": "text/csv"})
    with pytest.raises(Exception, match="persisted"):
        asyncio.run(upload_dataset(candidate, db, get_settings()))
    db.close()
    assert not list((get_settings().dataset_storage_root / "uploads").glob("*.csv"))
