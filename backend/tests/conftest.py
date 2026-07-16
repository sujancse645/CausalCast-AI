import os
import shutil
import tempfile
from pathlib import Path

os.environ["APP_ENV"] = "test"
TEST_ROOT = Path(tempfile.mkdtemp(prefix="causalcast-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT / 'test.db').as_posix()}"
os.environ["DATASET_STORAGE_ROOT"] = str(TEST_ROOT / "storage")
os.environ["PREPARATION_STORAGE_ROOT"] = str(TEST_ROOT / "processed")
os.environ["FORECAST_ARTIFACT_ROOT"] = str(TEST_ROOT / "artifacts")
os.environ["FORECAST_MIN_TRAIN_PERIODS"] = "4"
os.environ["FORECAST_MIN_VALIDATION_PERIODS"] = "1"
os.environ["FORECAST_MIN_TEST_PERIODS"] = "1"
os.environ["PREPARATION_MIN_PERIODS"] = "6"
os.environ["PREPARATION_MIN_TRAIN_ROWS"] = "4"
os.environ["PREPARATION_MIN_VALIDATION_ROWS"] = "1"
os.environ["PREPARATION_MIN_TEST_ROWS"] = "1"

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


@pytest.fixture(autouse=True)
def clean_database() -> None:
    yield
    from app.core.database import SessionLocal
    from app.models.dataset import Dataset
    from app.models.forecasting import (
        ForecastEvaluation,
        ForecastExperiment,
        ForecastModelRun,
        ForecastPredictionArtifact,
        ForecastTuningTrial,
    )
    from app.models.preparation import PreparationEvent, PreparedDataset, PreparedFeature
    from app.models.quality import DatasetQualityFinding, DatasetQualityReport
    from app.models.schema_profile import DatasetColumnProfile, DatasetSchemaProfile, SchemaMappingAudit

    with SessionLocal() as db:
        for model in (
            ForecastPredictionArtifact,
            ForecastTuningTrial,
            ForecastEvaluation,
            ForecastModelRun,
            ForecastExperiment,
            PreparationEvent,
            PreparedFeature,
            PreparedDataset,
            DatasetQualityFinding,
            DatasetQualityReport,
            SchemaMappingAudit,
            DatasetColumnProfile,
            DatasetSchemaProfile,
            Dataset,
        ):
            db.query(model).delete()
        db.commit()
    storage = TEST_ROOT / "storage"
    for path in storage.rglob("*") if storage.exists() else []:
        if path.is_file():
            path.unlink()
    shutil.rmtree(TEST_ROOT / "processed", ignore_errors=True)
    shutil.rmtree(TEST_ROOT / "artifacts", ignore_errors=True)
