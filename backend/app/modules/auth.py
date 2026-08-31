from datetime import UTC, datetime, timedelta
from time import monotonic

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_refresh_token,
    new_refresh_token,
    password_hasher,
)
from app.models import RefreshSession, User

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)
login_attempts: dict[str, list[float]] = {}


def enforce_login_rate_limit(key: str) -> None:
    now = monotonic()
    attempts = [at for at in login_attempts.get(key, []) if now - at < 60]
    if len(attempts) >= 8:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="请稍后再试")
    attempts.append(now)
    login_attempts[key] = attempts


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


async def get_owner(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录")
    user_id = decode_access_token(credentials.credentials)
    user = await session.scalar(select(User).where(User.id == user_id, User.is_owner.is_(True)))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner 会话无效")
    return user


async def issue_session(
    response: Response, user: User, session: AsyncSession, settings: Settings
) -> TokenResponse:
    raw_refresh = new_refresh_token()
    session.add(
        RefreshSession(
            owner_user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await session.commit()
    response.set_cookie(
        key="varbaia_refresh",
        value=raw_refresh,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.refresh_token_days * 86400,
        path="/api/auth",
    )
    return TokenResponse(access_token=create_access_token(user.id, settings))


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    enforce_login_rate_limit(
        f"{request.client.host if request.client else 'unknown'}:{payload.email}"
    )
    user = await session.scalar(select(User).where(User.email == payload.email.lower()))
    try:
        valid = user is not None and password_hasher.verify(user.password_hash, payload.password)
    except Exception:
        valid = False
    if not valid or not user or not user.is_owner:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码不正确")
    return await issue_session(response, user, session, settings)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    varbaia_refresh: str | None = Cookie(default=None),
) -> TokenResponse:
    # Cookie extraction remains explicit to keep tests and alternate clients deterministic.
    if not varbaia_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh 会话不存在")
    record = await session.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_refresh_token(varbaia_refresh)
        )
    )
    if record is None or record.revoked_at or record.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh 会话已失效")
    user = await session.scalar(select(User).where(User.id == record.owner_user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner 不存在")
    record.revoked_at = datetime.now(UTC)
    await session.flush()
    return await issue_session(response, user, session, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
    varbaia_refresh: str | None = Cookie(default=None),
) -> Response:
    if varbaia_refresh:
        record = await session.scalar(
            select(RefreshSession).where(
                RefreshSession.owner_user_id == owner.id,
                RefreshSession.token_hash == hash_refresh_token(varbaia_refresh),
            )
        )
        if record and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            await session.commit()
    response.delete_cookie("varbaia_refresh", path="/api/auth")
    return response
