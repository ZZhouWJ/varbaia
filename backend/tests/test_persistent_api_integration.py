import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest
from argon2 import PasswordHasher
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

if os.getenv("RUN_DB_TESTS") != "1":
    pytest.skip("需要 RUN_DB_TESTS=1 的本地 PostgreSQL", allow_module_level=True)

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.security import create_access_token
from app.main import app
from app.models import (
    DictationAttempt,
    ImportJobRecord,
    JobEvent,
    LearnerMemoryItem,
    MediaAsset,
    ProgressRecord,
    RolePlayMessage,
    RolePlaySession,
    TranscriptSegmentRecord,
    User,
    VocabularyItem,
    WritingAttempt,
)
from app.modules.role_play_tasks import evaluate_role_play
from app.modules.writing_tasks import evaluate_writing
from app.providers.ai import RolePlayFeedback, WritingEvaluation


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
    headers = {
        "Authorization": f"Bearer {create_access_token(user.id)}",
        "X-Request-ID": "persistent-import-test",
    }
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
            listed = await client.get("/api/owner/immersion/imports", headers=headers)
            assert listed.status_code == 200
            assert any(item["id"] == job_id for item in listed.json())
            cancelled = await client.post(
                f"/api/owner/immersion/imports/{job_id}/cancel", headers=headers
            )
            assert cancelled.status_code == 200
            assert cancelled.json()["status"] == "cancelled"
            assert cancelled.json()["message"] == "导入已取消"
            events = await client.get(
                f"/api/owner/immersion/imports/{job_id}/events", headers=headers
            )
            assert events.json()[-1]["status"] == "cancelled"
            retried = await client.post(
                f"/api/owner/immersion/imports/{job_id}/retry", headers=headers
            )
            assert retried.status_code == 202
            assert retried.json()["status"] == "queued"
    finally:
        async with SessionLocal() as session:
            job_ids = select(ImportJobRecord.id).where(ImportJobRecord.owner_user_id == user.id)
            await session.execute(delete(JobEvent).where(JobEvent.job_id.in_(job_ids)))
            await session.execute(
                delete(ImportJobRecord).where(ImportJobRecord.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_save_and_read_writing_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_evaluate_writing(_self: object, _prompt: str, _draft: str) -> WritingEvaluation:
        return WritingEvaluation(
            clarity_score=88,
            corrected_draft="I travelled by train.",
            suggestions=["Add one specific detail."],
        )

    monkeypatch.setattr(
        "app.providers.ai.ExternalHttpProvider.evaluate_writing", fake_evaluate_writing
    )
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
            assert result.result == "complete"
            found = await client.get(
                f"/api/owner/writing/attempts/{created.json()['id']}", headers=headers
            )
            assert found.status_code == 200
            assert found.json()["draft"] == "I travelled by train."
            assert found.json()["evaluation_status"] == "complete"
            assert found.json()["clarity_score"] == 88
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
            listed = await client.get("/api/owner/vocabulary/items", headers=headers)
            assert listed.status_code == 200
            assert any(item["id"] == item_id for item in listed.json())
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


@pytest.mark.asyncio
async def test_owner_can_manage_learner_memory() -> None:
    user = User(
        email=f"memory-{uuid4()}@example.com",
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
                "/api/owner/memory",
                headers=headers,
                json={
                    "category": "grammar",
                    "title": "第三人称单数",
                    "detail": "说现在时的时候检查动词是否需要 -s。",
                },
            )
            assert created.status_code == 201
            memory_id = created.json()["id"]
            listed = await client.get("/api/owner/memory", headers=headers)
            assert [item["id"] for item in listed.json()] == [memory_id]
            mastered = await client.post(f"/api/owner/memory/{memory_id}/master", headers=headers)
            assert mastered.status_code == 200
            assert mastered.json()["status"] == "mastered"
            assert (await client.get("/api/owner/memory", headers=headers)).json() == []
            deleted = await client.delete(f"/api/owner/memory/{memory_id}", headers=headers)
            assert deleted.status_code == 204
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(LearnerMemoryItem).where(LearnerMemoryItem.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_create_role_play_session_and_turn() -> None:
    user = User(
        email=f"role-play-{uuid4()}@example.com",
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
                "/api/owner/role-play/sessions",
                headers=headers,
                json={"scenario": "Ordering coffee at a busy cafe"},
            )
            assert created.status_code == 201
            session_id = created.json()["id"]
            turn = await client.post(
                f"/api/owner/role-play/sessions/{session_id}/turns",
                headers=headers,
                json={"learner_message": "Could I have a latte, please?"},
            )
            assert turn.status_code == 202
            assert turn.json()["status"] == "waiting_for_reply"
            assert turn.json()["messages"][0]["speaker"] == "learner"
    finally:
        async with SessionLocal() as session:
            session_ids = select(RolePlaySession.id).where(
                RolePlaySession.owner_user_id == user.id
            )
            await session.execute(
                delete(RolePlayMessage).where(RolePlayMessage.session_id.in_(session_ids))
            )
            await session.execute(
                delete(RolePlaySession).where(RolePlaySession.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_complete_role_play_and_read_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_evaluate_role_play(
        _self: object, _scenario: str, _conversation: list[dict[str, str]]
    ) -> RolePlayFeedback:
        return RolePlayFeedback(
            task_completion=90,
            grammar=85,
            vocabulary=82,
            fluency=80,
            pronunciation=None,
            naturalness=88,
            key_corrections=["Use 'a latte' after 'have'."],
            better_expressions=["Could I get a latte, please?"],
        )

    monkeypatch.setattr(
        "app.providers.ai.ExternalHttpProvider.evaluate_role_play", fake_evaluate_role_play
    )
    user = User(
        email=f"role-feedback-{uuid4()}@example.com",
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
                "/api/owner/role-play/sessions",
                headers=headers,
                json={"scenario": "Ordering coffee at a busy cafe"},
            )
            session_id = created.json()["id"]
            turn = await client.post(
                f"/api/owner/role-play/sessions/{session_id}/turns",
                headers=headers,
                json={"learner_message": "Could I have latte, please?"},
            )
            assert turn.status_code == 202
            completing = await client.post(
                f"/api/owner/role-play/sessions/{session_id}/complete", headers=headers
            )
            assert completing.status_code == 202
            assert completing.json()["status"] == "evaluating"
            await engine.dispose()
            result = await asyncio.to_thread(evaluate_role_play.apply, args=[session_id])
            assert result.result == "complete"
            found = await client.get(
                f"/api/owner/role-play/sessions/{session_id}", headers=headers
            )
            assert found.status_code == 200
            assert found.json()["status"] == "complete"
            assert found.json()["feedback"] == {
                "task_completion": 90,
                "grammar": 85,
                "vocabulary": 82,
                "fluency": 80,
                "pronunciation": None,
                "naturalness": 88,
                "key_corrections": ["Use 'a latte' after 'have'."],
                "better_expressions": ["Could I get a latte, please?"],
            }
    finally:
        async with SessionLocal() as session:
            session_ids = select(RolePlaySession.id).where(
                RolePlaySession.owner_user_id == user.id
            )
            await session.execute(
                delete(RolePlayMessage).where(RolePlayMessage.session_id.in_(session_ids))
            )
            await session.execute(
                delete(RolePlaySession).where(RolePlaySession.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_read_only_own_role_play_tts_audio() -> None:
    owner = User(
        email=f"role-audio-owner-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    other = User(
        email=f"role-audio-other-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    stored_name = f"role-play-integration-{uuid4()}.wav"
    root = Path(get_settings().media_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / stored_name).write_bytes(b"RIFFfixture-wav")
    try:
        async with SessionLocal() as session:
            session.add_all([owner, other])
            await session.commit()
            await session.refresh(owner)
            await session.refresh(other)
            role_session = RolePlaySession(owner_user_id=owner.id, scenario="Ordering coffee")
            session.add(role_session)
            await session.commit()
            await session.refresh(role_session)
            message = RolePlayMessage(
                session_id=role_session.id,
                speaker="assistant",
                content="Hello, what would you like?",
                coaching_tip="Use a polite request.",
                audio_stored_name=stored_name,
                audio_mime_type="audio/wav",
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
        owner_headers = {"Authorization": f"Bearer {create_access_token(owner.id)}"}
        other_headers = {"Authorization": f"Bearer {create_access_token(other.id)}"}
        url = f"/api/owner/role-play/sessions/{role_session.id}/messages/{message.id}/audio"
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            found = await client.get(url, headers=owner_headers)
            assert found.status_code == 200
            assert found.headers["content-type"] == "audio/wav"
            assert found.content == b"RIFFfixture-wav"
            denied = await client.get(url, headers=other_headers)
            assert denied.status_code == 404
    finally:
        async with SessionLocal() as session:
            session_ids = select(RolePlaySession.id).where(
                RolePlaySession.owner_user_id.in_([owner.id, other.id])
            )
            await session.execute(
                delete(RolePlayMessage).where(RolePlayMessage.session_id.in_(session_ids))
            )
            await session.execute(
                delete(RolePlaySession).where(RolePlaySession.id.in_(session_ids))
            )
            await session.execute(delete(User).where(User.id.in_([owner.id, other.id])))
            await session.commit()
        (root / stored_name).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_owner_can_upload_and_range_stream_media() -> None:
    user = User(
        email=f"media-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    async with SessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    stored_name: str | None = None
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            uploaded = await client.post(
                "/api/owner/immersion/uploads",
                headers=headers,
                files={"video": ("fixture.mp4", b"\x00\x00\x00\x18ftypisomfake", "video/mp4")},
            )
            assert uploaded.status_code == 202
            assert uploaded.json()["media_asset_id"]
            async with SessionLocal() as session:
                asset = await session.scalar(
                    select(MediaAsset).where(MediaAsset.import_job_id == uploaded.json()["id"])
                )
                assert asset is not None
                stored_name = asset.stored_name
                asset_id = asset.id
            streamed = await client.get(
                f"/api/owner/immersion/media/{asset_id}",
                headers={**headers, "Range": "bytes=4-9"},
            )
            assert streamed.status_code == 206
            assert streamed.headers["content-range"] == "bytes 4-9/16"
            assert streamed.content == b"ftypis"
            deleted = await client.delete(
                f"/api/owner/immersion/media/{asset_id}", headers=headers
            )
            assert deleted.status_code == 204
            unavailable = await client.get(
                f"/api/owner/immersion/media/{asset_id}", headers=headers
            )
            assert unavailable.status_code == 404
            stored_name = None
    finally:
        async with SessionLocal() as session:
            assets = (
                await session.scalars(select(MediaAsset).where(MediaAsset.owner_user_id == user.id))
            ).all()
            for asset in assets:
                stored_name = asset.stored_name
            await session.execute(delete(MediaAsset).where(MediaAsset.owner_user_id == user.id))
            await session.execute(
                delete(ImportJobRecord).where(ImportJobRecord.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()
        if stored_name:
            (Path(get_settings().media_root) / stored_name).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_owner_can_replace_and_read_transcript_segments() -> None:
    user = User(
        email=f"transcript-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    async with SessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        job = ImportJobRecord(owner_user_id=user.id, source_url="https://www.youtube.com/watch?v=fixture")
        session.add(job)
        await session.commit()
        await session.refresh(job)
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    payload = {
        "segments": [
            {"start_ms": 0, "end_ms": 1200, "text": "Welcome back.", "order": 0},
            {"start_ms": 1200, "end_ms": 2600, "text": "Let us practise English.", "order": 1},
        ]
    }
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            saved = await client.put(
                f"/api/owner/immersion/imports/{job.id}/transcript",
                headers=headers,
                json=payload,
            )
            assert saved.status_code == 200
            found = await client.get(
                f"/api/owner/immersion/imports/{job.id}/transcript", headers=headers
            )
            assert found.status_code == 200
            assert [item["text"] for item in found.json()] == [
                "Welcome back.",
                "Let us practise English.",
            ]
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(TranscriptSegmentRecord).where(
                    TranscriptSegmentRecord.import_job_id == job.id
                )
            )
            await session.execute(delete(ImportJobRecord).where(ImportJobRecord.id == job.id))
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()


@pytest.mark.asyncio
async def test_owner_can_submit_persistent_dictation_attempt() -> None:
    user = User(
        email=f"dictation-{uuid4()}@example.com",
        password_hash=PasswordHasher().hash("long-test-password"),
    )
    async with SessionLocal() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            result = await client.post(
                "/api/owner/dictation/attempts",
                headers=headers,
                json={
                    "answer": "Learning takes practice",
                    "reference": "Learning takes daily practice",
                },
            )
            assert result.status_code == 201
            assert result.json()["score"] == 75
            assert result.json()["missed_words"] == ["daily"]
        async with SessionLocal() as session:
            attempt = await session.scalar(
                select(DictationAttempt).where(DictationAttempt.owner_user_id == user.id)
            )
            assert attempt is not None
            assert attempt.score == 75
    finally:
        async with SessionLocal() as session:
            await session.execute(
                delete(DictationAttempt).where(DictationAttempt.owner_user_id == user.id)
            )
            await session.execute(delete(User).where(User.id == user.id))
            await session.commit()
