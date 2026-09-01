"""Celery tasks that persist external English-writing feedback."""

import asyncio
import json
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import WritingAttempt
from app.providers.ai import ExternalHttpProvider


async def _evaluate(attempt_id: UUID) -> str:
    try:
        async with SessionLocal() as session:
            attempt = await session.scalar(
                select(WritingAttempt).where(WritingAttempt.id == attempt_id)
            )
            if attempt is None:
                return "missing"
            if attempt.evaluation_status == "complete":
                return "complete"
            attempt.evaluation_status = "processing"
            attempt.evaluation_error = None
            await session.commit()
            try:
                result = await ExternalHttpProvider(get_settings()).evaluate_writing(
                    attempt.prompt, attempt.draft
                )
            except Exception as exc:
                attempt.evaluation_status = "failed"
                attempt.evaluation_error = str(exc)[:500]
                await session.commit()
                return "failed"
            attempt.clarity_score = max(0, min(100, result.clarity_score))
            attempt.feedback_json = json.dumps(
                {
                    "corrected_draft": result.corrected_draft,
                    "suggestions": result.suggestions,
                },
                ensure_ascii=False,
            )
            attempt.evaluation_status = "complete"
            await session.commit()
            return "complete"
    finally:
        await engine.dispose()


@celery_app.task(name="writing.evaluate", acks_late=True)
def evaluate_writing(attempt_id: str) -> str:
    return asyncio.run(_evaluate(UUID(attempt_id)))
