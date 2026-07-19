from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    username = settings.development_username
    password = settings.development_password
    if settings.app_env == "production" or not username or not password:
        raise HTTPException(status_code=404, detail="Not found")
    valid = secrets.compare_digest(form_data.username, username) and secrets.compare_digest(
        form_data.password, password
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(subject=username), token_type="bearer")


@router.post("/login/developer", response_model=TokenResponse)
async def login_developer_token(settings: Annotated[Settings, Depends(get_settings)]) -> TokenResponse:
    """Issue a local development token; this route is unavailable in production."""
    if settings.app_env == "production":
        raise HTTPException(status_code=404, detail="Not found")
    return TokenResponse(access_token=create_access_token(subject="developer"), token_type="bearer")
