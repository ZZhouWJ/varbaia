import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings

password_hasher = PasswordHasher()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def create_access_token(user_id: UUID, settings: Settings | None = None) -> str:
    active_settings = settings or get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "typ": "access",
        "iat": now,
        "exp": now + timedelta(minutes=active_settings.access_token_minutes),
    }
    return jwt.encode(payload, active_settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str, settings: Settings | None = None) -> UUID:
    active_settings = settings or get_settings()
    try:
        payload = jwt.decode(token, active_settings.jwt_secret, algorithms=["HS256"])
        if payload.get("typ") != "access":
            raise ValueError("wrong token type")
        return UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
