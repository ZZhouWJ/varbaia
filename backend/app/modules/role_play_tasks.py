"""Celery task for external English role-play replies."""

import asyncio
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import RolePlayMessage, RolePlaySession
from app.providers.ai import ExternalHttpProvider


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
                reply = await ExternalHttpProvider(get_settings()).reply_to_role_play(
                    session.scenario, conversation
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
