import asyncio
import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import PronunciationAttempt
from app.providers.ai import ExternalHttpProvider


async def _evaluate(attempt_id: UUID) -> str:
    try:
        async with SessionLocal() as session:
            attempt = await session.scalar(
                select(PronunciationAttempt).where(PronunciationAttempt.id == attempt_id)
            )
            if attempt is None or attempt.evaluation_status == "complete":
                return "missing" if attempt is None else "complete"
            attempt.evaluation_status = "processing"
            attempt.evaluation_error = None
            await session.commit()
            try:
                result = await ExternalHttpProvider(get_settings()).evaluate_pronunciation(
                    str(Path(get_settings().media_root).resolve() / attempt.stored_name),
                    attempt.reference_text,
                )
            except Exception as exc:
                attempt.evaluation_status = "failed"
                attempt.evaluation_error = str(exc)[:500]
                await session.commit()
                return "failed"
            attempt.result_json = json.dumps(result, ensure_ascii=False)
            attempt.evaluation_status = "complete"
            await session.commit()
            return "complete"
    finally:
        await engine.dispose()


@celery_app.task(name="pronunciation.evaluate", acks_late=True)
def evaluate_pronunciation(attempt_id: str) -> str:
    return asyncio.run(_evaluate(UUID(attempt_id)))
