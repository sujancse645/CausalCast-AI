from app.core.config import Settings
from app.core.database import database_is_connected, database_type
from app.schemas.system import ApplicationInfo, BackendInfo, DatabaseInfo, ModulesInfo, SystemInfoResponse


def get_system_info(settings: Settings) -> SystemInfoResponse:
    connected = database_is_connected()
    return SystemInfoResponse(
        application=ApplicationInfo(
            name=settings.app_name,
            version=settings.app_version,
            environment=settings.app_env,
        ),
        backend=BackendInfo(),
        database=DatabaseInfo(
            type=database_type(settings.database_url),
            status="connected" if connected else "unavailable",
        ),
        modules=ModulesInfo(),
    )
