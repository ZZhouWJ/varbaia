"""Celery entrypoints for restart-safe immersion import work."""

import asyncio
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.tasks import celery_app
from app.models import ImportJobRecord, JobEvent, MediaAsset, TranscriptSegmentRecord
from app.modules.immersion.downloader import download_remote_video
from app.providers.ai import ExternalHttpProvider

STEPS = [
    ("validating", 8, "正在验证导入地址"),
    ("fetching_metadata", 18, "正在读取视频元数据"),
    ("transcribing", 58, "正在请求英语转写服务"),
    ("segmenting", 86, "正在生成可练习片段"),
    ("ready", 100, "学习材料已就绪"),
]


async def _advance(job_id: UUID, request_id: str | None) -> str:
    try:
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
            if next_status == "fetching_metadata" and not job.source_url.startswith("upload://"):
                existing_media = await session.scalar(
                    select(MediaAsset.id).where(MediaAsset.import_job_id == job.id)
                )
                if existing_media is None:
                    settings = get_settings()
                    try:
                        stored_name, size_bytes = await download_remote_video(
                            source_url=job.source_url,
                            media_root=Path(settings.media_root).resolve(),
                            stored_stem=str(uuid4()),
                            max_bytes=settings.max_upload_mb * 1024 * 1024,
                        )
                    except Exception as exc:
                        job.status, job.progress = "failed", progress
                        session.add(
                            JobEvent(
                                job_id=job.id,
                                status="failed",
                                progress=progress,
                                message=f"视频下载失败：{str(exc)[:180]}",
                                request_id=request_id,
                            )
                        )
                        await session.commit()
                        return "failed"
                    await session.refresh(job)
                    if job.status == "cancelled":
                        (Path(settings.media_root).resolve() / stored_name).unlink(missing_ok=True)
                        return "cancelled"
                    session.add(
                        MediaAsset(
                            owner_user_id=job.owner_user_id,
                            import_job_id=job.id,
                            stored_name=stored_name,
                            mime_type="video/mp4" if stored_name.endswith(".mp4") else "video/webm",
                            size_bytes=size_bytes,
                        )
                    )
                    await session.commit()
            if next_status == "transcribing":
                existing_transcript = await session.scalar(
                    select(TranscriptSegmentRecord.id).where(
                        TranscriptSegmentRecord.import_job_id == job.id
                    )
                )
                if existing_transcript is not None:
                    return next_status
                try:
                    provider = ExternalHttpProvider(get_settings())
                    segments = await provider.transcribe_english(job.source_url)
                except Exception as exc:
                    job.status, job.progress = "failed", progress
                    session.add(
                        JobEvent(
                            job_id=job.id,
                            status="failed",
                            progress=progress,
                            message=f"英语转写失败：{str(exc)[:180]}",
                            request_id=request_id,
                        )
                    )
                    await session.commit()
                    return "failed"
                await session.refresh(job)
                if job.status == "cancelled":
                    return "cancelled"
                await session.execute(
                    delete(TranscriptSegmentRecord).where(
                        TranscriptSegmentRecord.import_job_id == job.id
                    )
                )
                session.add_all(
                    TranscriptSegmentRecord(
                        import_job_id=job.id,
                        position=index,
                        start_ms=round(_seconds(segment.get("start")) * 1000),
                        end_ms=round(_seconds(segment.get("end")) * 1000),
                        text=str(segment["text"]),
                    )
                    for index, segment in enumerate(segments)
                    if _seconds(segment.get("end")) > _seconds(segment.get("start"))
                )
                await session.commit()
            return next_status
    finally:
        await engine.dispose()


def _seconds(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise ValueError("转写片段缺少有效时间戳")
    return float(value)


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
