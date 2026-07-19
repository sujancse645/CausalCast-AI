from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.authz import Role, UserContext
from app.core.config import get_settings
from app.core.security import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_v1_prefix}/auth/login")


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserContext:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise _credentials_exception()

        # In a real application, we would fetch the user from the database here
        # For now, we extract roles and tenant_id from the JWT payload
        tenant_id: str = payload.get("tenant_id", "default-tenant")
        roles = payload.get("roles", [Role.ADMIN.value])

        return UserContext(user_id=user_id, tenant_id=tenant_id, roles=[Role(r) for r in roles])
    except (JWTError, ValidationError):
        raise _credentials_exception() from None
