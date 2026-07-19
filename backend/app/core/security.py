import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import cast

from jose import jwt
from passlib.context import CryptContext

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(48)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return cast(bool, PWD_CONTEXT.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    # Enforce basic password policy before hashing
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long")
    return cast(str, PWD_CONTEXT.hash(password))


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return cast(str, encoded_jwt)
