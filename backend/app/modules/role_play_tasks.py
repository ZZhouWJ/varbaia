"""Celery task for external English role-play replies."""

import asyncio
import json
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import RolePlayMessage, RolePlaySession
from app.providers.ai import ExternalHttpProvider
from app.providers.tencent_speech import TencentEnglishSpeechProvider


async def _reply(session_id: UUID) -> str:
    try:
        async with SessionLocal() as db:
            session = await db.scalar(
                select(RolePlaySession).where(RolePlaySession.id == session_id)
            )
            if session is None:
                return "missing"
            if session.status != "waiting_for_reply":
                return session.status
            messages = (
                await db.scalars(
                    select(RolePlayMessage)
                    .where(RolePlayMessage.session_id == session.id)
                    .order_by(RolePlayMessage.created_at)
                )
            ).all()
            conversation = [
                {"speaker": message.speaker, "content": message.content} for message in messages
            ]
            try:
                settings = get_settings()
                reply = await ExternalHttpProvider(settings).reply_to_role_play(
                    session.scenario, conversation
                )
                speech = await TencentEnglishSpeechProvider(settings).synthesize_english(
                    reply.reply
                )
            except Exception:
                session.status = "failed"
                await db.commit()
                return "failed"
            db.add(
                RolePlayMessage(
                    session_id=session.id,
                    speaker="assistant",
                    content=reply.reply,
                    coaching_tip=reply.coaching_tip,
                    audio_stored_name=_store_reply_audio(speech.wav_bytes),
                    audio_mime_type="audio/wav",
                )
            )
            session.status = "active"
            await db.commit()
            return "active"
    finally:
        await engine.dispose()


@celery_app.task(name="role_play.reply", acks_late=True)
def reply_to_role_play(session_id: str) -> str:
    return asyncio.run(_reply(UUID(session_id)))


async def _evaluate_session(session_id: UUID) -> str:
    try:
        async with SessionLocal() as db:
            session = await db.scalar(
                select(RolePlaySession).where(RolePlaySession.id == session_id)
            )
            if session is None:
                return "missing"
            if session.status == "complete":
                return "complete"
            messages = (
                await db.scalars(
                    select(RolePlayMessage)
                    .where(RolePlayMessage.session_id == session.id)
                    .order_by(RolePlayMessage.created_at)
                )
            ).all()
            conversation = [
                {"speaker": message.speaker, "content": message.content} for message in messages
            ]
            try:
                feedback = await ExternalHttpProvider(get_settings()).evaluate_role_play(
                    session.scenario, conversation
                )
            except Exception:
                session.status = "failed"
                await db.commit()
                return "failed"
            session.feedback_json = json.dumps(
                {
                    "task_completion": feedback.task_completion,
                    "grammar": feedback.grammar,
                    "vocabulary": feedback.vocabulary,
                    "fluency": feedback.fluency,
                    "pronunciation": feedback.pronunciation,
                    "naturalness": feedback.naturalness,
                    "key_corrections": feedback.key_corrections,
                    "better_expressions": feedback.better_expressions,
                },
                ensure_ascii=False,
            )
            session.status = "complete"
            await db.commit()
            return "complete"
    finally:
        await engine.dispose()


@celery_app.task(name="role_play.evaluate", acks_late=True)
def evaluate_role_play(session_id: str) -> str:
    return asyncio.run(_evaluate_session(UUID(session_id)))


def _store_reply_audio(wav_bytes: bytes) -> str:
    root = Path(get_settings().media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    name = f"role-play-{uuid4()}.wav"
    (root / name).write_bytes(wav_bytes)
    return name
