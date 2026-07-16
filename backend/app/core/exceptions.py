import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class DatasetError(Exception):
    """Base class for safe dataset-domain errors."""


class DatasetNotFoundError(DatasetError):
    pass


class DatasetTooLargeError(DatasetError):
    pass


class UnsupportedDatasetTypeError(DatasetError):
    pass


class InvalidDatasetError(DatasetError):
    pass


class DuplicateDatasetError(DatasetError):
    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__("This file has already been uploaded")


class DatasetStorageError(DatasetError):
    pass


class DatasetParseError(DatasetError):
    pass


class DatasetSchemaNotFoundError(DatasetError):
    pass


class DatasetNotReadyForSchemaError(DatasetError):
    pass


class SchemaInferenceError(DatasetError):
    pass


class ColumnProfileNotFoundError(DatasetError):
    pass


class InvalidSemanticRoleError(DatasetError):
    pass


class SchemaConfirmationError(DatasetError):
    def __init__(self, issues: list[str]) -> None:
        self.issues = issues
        super().__init__("Schema mapping has unresolved blocking issues")


class SchemaVersionConflictError(DatasetError):
    pass


class QualityReportNotFoundError(DatasetError):
    pass


class DatasetNotReadyForQualityAnalysisError(DatasetError):
    pass


class QualityAnalysisError(DatasetError):
    pass


class MissingConfirmedSchemaError(DatasetError):
    pass


class QualityVersionConflictError(DatasetError):
    pass


class UnsupportedQualityOperationError(DatasetError):
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error for %s", request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
