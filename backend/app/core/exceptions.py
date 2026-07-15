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


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error for %s", request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
