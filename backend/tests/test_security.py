from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_refresh_token,
    new_refresh_token,
)


def test_access_token_round_trip_and_refresh_token_entropy() -> None:
    settings = Settings(jwt_secret="x" * 32)
    user_id = uuid4()
    assert decode_access_token(create_access_token(user_id, settings), settings) == user_id
    assert hash_refresh_token(new_refresh_token()) != hash_refresh_token(new_refresh_token())


def test_rejects_invalid_access_token() -> None:
    with pytest.raises(HTTPException) as error:
        decode_access_token("not-a-token", Settings(jwt_secret="x" * 32))
    assert error.value.status_code == 401
