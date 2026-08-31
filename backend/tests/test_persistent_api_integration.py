import os
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

if os.getenv("RUN_DB_TESTS") != "1":
    pytest.skip("需要 RUN_DB_TESTS=1 的本地 PostgreSQL", allow_module_level=True)

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models import ImportJobRecord, User


@pytest.mark.asyncio
async def test_owner_can_create_and_read_persistent_import() -> None:
    user = User(
        email=f"integration-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    async with SessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            created = await client.post(
                "/api/owner/immersion/imports",
                headers=headers,
                json={"source_url": "https://www.youtube.com/watch?v=fixture", "accent": "en-US"},
            )
            assert created.status_code == 202
            job_id = created.json()["id"]
            found = await client.get(f"/api/owner/immersion/imports/{job_id}", headers=headers)
            assert found.status_code == 200
            assert found.json()["id"] == job_id
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(ImportJobRecord).where(ImportJobRecord.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()
