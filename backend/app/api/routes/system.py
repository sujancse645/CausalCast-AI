from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.system import SystemInfoResponse
from app.services.system_service import get_system_info

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse)
def system_info(settings: Annotated[Settings, Depends(get_settings)]) -> SystemInfoResponse:
    return get_system_info(settings)
