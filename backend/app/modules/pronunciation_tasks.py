import asyncio
import json
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import PronunciationAttempt
from app.modules.learner_memory import record_signal
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
                attempt.evaluation_error = _public_evaluation_error(exc.category)
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
            if (
                assessment.pronunciation_accuracy is not None
                and assessment.pronunciation_accuracy < 75
            ):
                await record_signal(
                    session,
                    owner_user_id=attempt.owner_user_id,
                    category="pronunciation",
                    memory_key="pronunciation-accuracy",
                    title="英语发音准确度",
                    detail="多次跟读的整体准确度低于 75 分；建议放慢速度并逐词重读。",
                    source_type="pronunciation",
                    severity=2 if assessment.pronunciation_accuracy < 55 else 1,
                )
            if (
                assessment.pronunciation_fluency is not None
                and assessment.pronunciation_fluency < 0.75
            ):
                await record_signal(
                    session,
                    owner_user_id=attempt.owner_user_id,
                    category="fluency",
                    memory_key="pronunciation-fluency",
                    title="英语表达流利度",
                    detail="多次跟读的流利度低于 0.75；建议使用短语块连续跟读。",
                    source_type="pronunciation",
                )
            attempt.evaluation_status = "complete"
            await session.commit()
            return "complete"
    finally:
        await engine.dispose()


@celery_app.task(name="pronunciation.evaluate", acks_late=True)
def evaluate_pronunciation(attempt_id: str) -> str:
    return asyncio.run(_evaluate(UUID(attempt_id)))


def _public_evaluation_error(category: str) -> str:
    messages = {
        "authentication_error": "发音评测鉴权不可用，请联系 Owner 检查服务配置。",
        "service_unavailable": "发音评测服务暂不可用，请稍后重试。",
        "invalid_audio": "录音格式或时长不符合要求，请重新录制。",
        "invalid_reference_text": "参考句子无效，请选择一条英文句子。",
        "websocket_error": "发音评测连接失败，请稍后重试。",
        "provider_timeout": "发音评测超时，请稍后重试。",
        "provider_rate_limit": "发音评测暂时繁忙，请稍后重试。",
    }
    return messages.get(category, "发音评测服务发生未预期错误。")
