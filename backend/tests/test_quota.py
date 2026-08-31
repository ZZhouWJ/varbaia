import pytest
from fastapi import HTTPException

from app.modules.immersion.quota import DiskBudget, enforce_disk_budget


def test_disk_budget_keeps_two_gib_safety_reserve() -> None:
    budget = DiskBudget(free_bytes=4 * 1024**3, estimated_media_bytes=1024**3)
    enforce_disk_budget(budget)


def test_disk_budget_rejects_insufficient_space() -> None:
    budget = DiskBudget(free_bytes=3 * 1024**3, estimated_media_bytes=1024**3)
    with pytest.raises(HTTPException) as error:
        enforce_disk_budget(budget)
    assert error.value.status_code == 422
