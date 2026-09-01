from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_refresh_token,
    new_refresh_token,
)
from app.modules.auth import enforce_cookie_origin


def test_access_token_round_trip_and_refresh_token_entropy() -> None:
    settings = Settings(jwt_secret="x" * 32)
    user_id = uuid4()
    assert decode_access_token(create_access_token(user_id, settings), settings) == user_id
    assert hash_refresh_token(new_refresh_token()) != hash_refresh_token(new_refresh_token())


def test_rejects_invalid_access_token() -> None:
    with pytest.raises(HTTPException) as error:
        decode_access_token("not-a-token", Settings(jwt_secret="x" * 32))
    assert error.value.status_code == 401


def test_cookie_origin_rejects_untrusted_browser_origin() -> None:
    settings = Settings(_env_file=None, cors_origins="https://app.example.com")
    request = Request({"type": "http", "headers": [(b"origin", b"https://attacker.example")]})

    with pytest.raises(HTTPException, match="不允许的请求来源"):
        enforce_cookie_origin(request, settings)


def test_cookie_origin_allows_owner_origin_and_non_browser_client() -> None:
    settings = Settings(_env_file=None, cors_origins="https://app.example.com")
    allowed = Request({"type": "http", "headers": [(b"origin", b"https://app.example.com")]})
    cli = Request({"type": "http", "headers": []})

    enforce_cookie_origin(allowed, settings)
    enforce_cookie_origin(cli, settings)
