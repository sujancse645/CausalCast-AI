import os
import shutil
import tempfile
from pathlib import Path

os.environ["APP_ENV"] = "test"
TEST_ROOT = Path(tempfile.mkdtemp(prefix="causalcast-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT / 'test.db').as_posix()}"
os.environ["DATASET_STORAGE_ROOT"] = str(TEST_ROOT / "storage")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402

Base.metadata.create_all(engine)


def pytest_sessionfinish() -> None:
    engine.dispose()
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
