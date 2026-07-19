from enum import StrEnum

from pydantic import BaseModel


class Role(StrEnum):
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SERVICE_ACCOUNT = "service_account"


class Permission(StrEnum):
    READ_DATASET = "read:dataset"
    WRITE_DATASET = "write:dataset"
    DELETE_DATASET = "delete:dataset"
    READ_MODEL = "read:model"
    TRAIN_MODEL = "train:model"
    MANAGE_ACCESS = "manage:access"
    MANAGE_AUDIT = "manage:audit"


ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],
    Role.DATA_SCIENTIST: [
        Permission.READ_DATASET,
        Permission.WRITE_DATASET,
        Permission.READ_MODEL,
        Permission.TRAIN_MODEL,
    ],
    Role.ANALYST: [Permission.READ_DATASET, Permission.READ_MODEL],
    Role.VIEWER: [Permission.READ_DATASET, Permission.READ_MODEL],
    Role.SERVICE_ACCOUNT: [p for p in Permission],
}


class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    roles: list[Role]
    is_active: bool = True
    mfa_verified: bool = False


def has_permission(user: UserContext, required_permission: Permission) -> bool:
    if not user.is_active:
        return False
    return any(required_permission in ROLE_PERMISSIONS.get(role, []) for role in user.roles)


def verify_tenant_access(user: UserContext, resource_tenant_id: str) -> bool:
    return user.tenant_id == resource_tenant_id
