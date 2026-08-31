import pytest
from fastapi import HTTPException

from app.modules.auth import enforce_login_rate_limit, login_attempts


def test_login_rate_limit_rejects_ninth_attempt() -> None:
    key = "test@example.com"
    login_attempts.pop(key, None)
    for _ in range(8):
        enforce_login_rate_limit(key)
    with pytest.raises(HTTPException) as error:
        enforce_login_rate_limit(key)
    assert error.value.status_code == 429
