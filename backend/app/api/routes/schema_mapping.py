from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import (
    ColumnProfileNotFoundError,
    DatasetNotReadyForSchemaError,
    DatasetSchemaNotFoundError,
    SchemaConfirmationError,
    SchemaInferenceError,
)
from app.schemas.schema_mapping import (
    ColumnMappingUpdateRequest,
    ColumnMappingUpdateResponse,
    DatasetSchemaDetail,
    SchemaConfirmationRequest,
    SchemaConfirmationResponse,
    SchemaHistoryResponse,
    SchemaInferenceRequest,
    SchemaInferenceResponse,
    SchemaRoleListResponse,
    SchemaStatsResponse,
    SemanticRoleDefinition,
)
from app.services.schema_inference_service import (
    confirm_schema,
    infer_schema,
    schema_detail,
    schema_history,
    schema_stats,
    update_mapping,
)
from app.services.semantic_role_registry import ROLE_DESCRIPTIONS, SemanticRole

router = APIRouter(tags=["schema mapping"])
Db = Annotated[Session, Depends(get_db)]
Config = Annotated[Settings, Depends(get_settings)]


@router.get("/schema/roles", response_model=SchemaRoleListResponse)
def roles() -> SchemaRoleListResponse:
    return SchemaRoleListResponse(
        items=[
            SemanticRoleDefinition(
                role=r.value, label=r.value.replace("_", " ").title(), description=ROLE_DESCRIPTIONS[r]
            )
            for r in SemanticRole
        ]
    )


@router.get("/datasets/schema/stats", response_model=SchemaStatsResponse)
def stats(db: Db) -> SchemaStatsResponse:
    return schema_stats(db)


@router.post(
    "/datasets/{dataset_id}/schema/infer", response_model=SchemaInferenceResponse, status_code=status.HTTP_201_CREATED
)
def infer(
    dataset_id: str, request: SchemaInferenceRequest, db: Db, settings: Config
) -> DatasetSchemaDetail | JSONResponse:
    try:
        return infer_schema(db, dataset_id, settings, request.reason)
    except DatasetSchemaNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except DatasetNotReadyForSchemaError as exc:
        return JSONResponse(status_code=409, content={"detail": str(exc)})
    except SchemaInferenceError:
        return JSONResponse(status_code=500, content={"detail": "Schema inference failed safely"})


@router.get("/datasets/{dataset_id}/schema", response_model=DatasetSchemaDetail)
def active(dataset_id: str, db: Db) -> DatasetSchemaDetail | JSONResponse:
    try:
        return schema_detail(db, dataset_id)
    except DatasetSchemaNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})


@router.get("/datasets/{dataset_id}/schema/history", response_model=SchemaHistoryResponse)
def history(dataset_id: str, db: Db) -> SchemaHistoryResponse:
    return schema_history(db, dataset_id)


@router.patch("/datasets/{dataset_id}/schema/columns/{column_profile_id}", response_model=ColumnMappingUpdateResponse)
def update_column(
    dataset_id: str, column_profile_id: str, request: ColumnMappingUpdateRequest, db: Db
) -> ColumnMappingUpdateResponse | JSONResponse:
    try:
        return update_mapping(db, dataset_id, column_profile_id, request.semantic_role, request.reason)
    except (DatasetSchemaNotFoundError, ColumnProfileNotFoundError) as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc)})


@router.post("/datasets/{dataset_id}/schema/confirm", response_model=SchemaConfirmationResponse)
def confirm(dataset_id: str, _request: SchemaConfirmationRequest, db: Db) -> SchemaConfirmationResponse | JSONResponse:
    try:
        return confirm_schema(db, dataset_id)
    except DatasetSchemaNotFoundError as exc:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    except SchemaConfirmationError as exc:
        return JSONResponse(status_code=422, content={"detail": str(exc), "issues": exc.issues})
