import asyncio
import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import PronunciationAttempt
from app.providers.audio_normalization import normalize_audio
from app.providers.pronunciation import PronunciationProviderError
from app.providers.tencent_soe_n_assessment import TencentSOENAdapter


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
                settings = get_settings()
                audio = await normalize_audio(
                    Path(settings.media_root).resolve() / attempt.stored_name, attempt.mime_type
                )
                assessment = await TencentSOENAdapter(settings).assess(
                    attempt.reference_text, audio
                )
            except PronunciationProviderError as exc:
                attempt.evaluation_status = "failed"
                attempt.evaluation_error = f"{exc.category}: {str(exc)}"[:500]
                await session.commit()
                return "failed"
            except Exception:
                attempt.evaluation_status = "failed"
                attempt.evaluation_error = "provider_business_error: 发音评测服务发生未预期错误。"
                await session.commit()
                return "failed"
            attempt.result_json = json.dumps(assessment.public_dict(), ensure_ascii=False)
            attempt.raw_provider_result_json = json.dumps(
                assessment.raw_provider_result, ensure_ascii=False
            )
            attempt.evaluation_status = "complete"
            await session.commit()
            return "complete"
    finally:
        await engine.dispose()


@celery_app.task(name="pronunciation.evaluate", acks_late=True)
def evaluate_pronunciation(attempt_id: str) -> str:
    return asyncio.run(_evaluate(UUID(attempt_id)))
