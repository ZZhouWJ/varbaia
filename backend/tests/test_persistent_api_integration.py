import asyncio
import os
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

if os.getenv("RUN_DB_TESTS") != "1":
    pytest.skip("需要 RUN_DB_TESTS=1 的本地 PostgreSQL", allow_module_level=True)

from app.core.database import SessionLocal, engine
from app.core.security import create_access_token
from app.main import app
from app.models import ImportJobRecord, ProgressRecord, User, VocabularyItem, WritingAttempt
from app.modules.writing_tasks import evaluate_writing


@pytest.fixture(autouse=True)
async def dispose_database_engine_between_tests():
    yield
    await engine.dispose()


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


@pytest.mark.asyncio
async def test_owner_can_save_and_read_writing_attempt() -> None:
    user = User(
        email=f"writing-{uuid4()}@example.com",
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
                "/api/owner/writing/attempts",
                headers=headers,
                json={"prompt": "Describe a memorable journey.", "draft": "I travelled by train."},
            )
            assert created.status_code == 202
            assert created.json()["evaluation_status"] == "queued"
            await engine.dispose()
            result = await asyncio.to_thread(
                evaluate_writing.apply, args=[created.json()["id"]]
            )
            assert result.result == "failed"
            found = await client.get(
                f"/api/owner/writing/attempts/{created.json()['id']}", headers=headers
            )
            assert found.status_code == 200
            assert found.json()["draft"] == "I travelled by train."
            assert found.json()["evaluation_status"] == "failed"
            assert "未配置外部 AI Provider" in found.json()["evaluation_error"]
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(WritingAttempt).where(WritingAttempt.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_create_and_review_vocabulary() -> None:
    user = User(
        email=f"vocabulary-{uuid4()}@example.com",
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
                "/api/owner/vocabulary/items",
                headers=headers,
                json={"term": "curious", "definition": "wanting to know more"},
            )
            assert created.status_code == 201
            item_id = created.json()["id"]
            due = await client.get("/api/owner/vocabulary/due", headers=headers)
            assert any(item["id"] == item_id for item in due.json())
            reviewed = await client.post(
                f"/api/owner/vocabulary/items/{item_id}/review/easy", headers=headers
            )
            assert reviewed.status_code == 200
            assert reviewed.json()["repetitions"] == 1
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(VocabularyItem).where(VocabularyItem.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_save_and_resume_learning_progress() -> None:
    user = User(
        email=f"progress-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    resource_id = uuid4()
    async with SessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    payload = {
        "resource_type": "immersion_video",
        "resource_id": str(resource_id),
        "completion_percent": 25,
        "last_position_seconds": 180,
    }
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            saved = await client.put("/api/owner/progress", headers=headers, json=payload)
            assert saved.status_code == 200
            updated = await client.put(
                "/api/owner/progress",
                headers=headers,
                json={**payload, "completion_percent": 80, "last_position_seconds": 600},
            )
            assert updated.status_code == 200
            found = await client.get(
                f"/api/owner/progress/immersion_video/{resource_id}", headers=headers
            )
            assert found.status_code == 200
            assert found.json()["completion_percent"] == 80
            assert found.json()["last_position_seconds"] == 600
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(ProgressRecord).where(ProgressRecord.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()
