"""Celery entrypoints for restart-safe immersion import work."""

import asyncio
from uuid import UUID

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.tasks import celery_app
from app.models import ImportJobRecord, JobEvent

STEPS = [
    ("validating", 8, "正在验证导入地址"),
    ("fetching_metadata", 18, "正在读取视频元数据"),
    ("transcribing", 58, "正在请求英语转写服务"),
    ("segmenting", 86, "正在生成可练习片段"),
    ("ready", 100, "学习材料已就绪"),
]


async def _advance(job_id: UUID, request_id: str | None) -> str:
    async with SessionLocal() as session:
        job = await session.scalar(select(ImportJobRecord).where(ImportJobRecord.id == job_id))
        if job is None:
            return "missing"
        if job.status in {"ready", "failed", "cancelled"}:
            return job.status
        index = next((i for i, step in enumerate(STEPS) if step[0] == job.status), -1)
        next_status, progress, message = STEPS[min(index + 1, len(STEPS) - 1)]
        job.status, job.progress = next_status, progress
        session.add(
            JobEvent(
                job_id=job.id,
                status=next_status,
                progress=progress,
                message=message,
                request_id=request_id,
            )
        )
        await session.commit()
        return next_status


@celery_app.task(
    bind=True,
    name="immersion.import_media",
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def import_media(self, job_id: str, request_id: str | None = None) -> str:
    """Advance one idempotent stage; production adapters perform media work per stage."""
    next_status = asyncio.run(_advance(UUID(job_id), request_id))
    if next_status not in {"missing", "ready", "failed", "cancelled"}:
        import_media.apply_async(args=[job_id, request_id], countdown=1)
    return next_status
