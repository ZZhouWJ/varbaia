import shutil
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models import ImportJobRecord, JobEvent, MediaAsset, TranscriptSegmentRecord, User
from app.modules.auth import get_owner
from app.modules.immersion.media import (
    iter_bytes,
    parse_range,
    safe_media_path,
    validate_media_signature,
)
from app.modules.immersion.quota import DiskBudget, enforce_disk_budget
from app.modules.immersion.schemas import (
    ImportJob,
    TranscriptReplace,
    TranscriptSegment,
    VideoImportRequest,
)
from app.modules.immersion.service import ImmersionService
from app.modules.immersion.subtitles import parse_subtitles
from app.modules.immersion.tasks import import_media

router = APIRouter(prefix="/owner/immersion", tags=["owner-immersion"])
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v"}


def to_schema(record: ImportJobRecord) -> ImportJob:
    if record.status == "ready":
        message = "学习材料已就绪"
    elif record.status == "failed":
        message = "导入失败，请查看任务事件"
    else:
        message = "任务处理中"
    return ImportJob(
        id=record.id,
        source_url=record.source_url,
        status=record.status,
        progress=record.progress,
        message=message,
        created_at=record.created_at,
    )


@router.post("/imports", response_model=ImportJob, status_code=status.HTTP_202_ACCEPTED)
async def create_persistent_import(
    payload: VideoImportRequest,
    request: Request,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> ImportJob:
    # Reuse central URL/SSRF validation without retaining an in-memory job.
    ImmersionService(get_settings()).validate_source_url(payload)
    job = ImportJobRecord(owner_user_id=owner.id, source_url=str(payload.source_url))
    session.add(job)
    await session.commit()
    await session.refresh(job)
    import_media.delay(str(job.id), request.headers.get("x-request-id"))
    return to_schema(job)


@router.get("/imports", response_model=list[ImportJob])
async def list_persistent_imports(
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> list[ImportJob]:
    jobs = (
        await session.scalars(
            select(ImportJobRecord)
            .where(ImportJobRecord.owner_user_id == owner.id)
            .order_by(ImportJobRecord.updated_at.desc())
        )
    ).all()
    return [to_schema(job) for job in jobs]


@router.get("/imports/{job_id}", response_model=ImportJob)
async def get_persistent_import(
    job_id: UUID,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> ImportJob:
    job = await session.scalar(
        select(ImportJobRecord).where(
            ImportJobRecord.id == job_id, ImportJobRecord.owner_user_id == owner.id
        )
    )
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到导入任务")
    return to_schema(job)


class ImportEventResponse(BaseModel):
    status: str
    progress: int
    message: str
    created_at: datetime


@router.get("/imports/{job_id}/events", response_model=list[ImportEventResponse])
async def list_import_events(
    job_id: UUID,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> list[ImportEventResponse]:
    await get_owned_import(job_id, owner.id, session)
    events = (
        await session.scalars(
            select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at)
        )
    ).all()
    return [ImportEventResponse.model_validate(event, from_attributes=True) for event in events]


async def get_owned_import(job_id: UUID, owner_id: UUID, session: AsyncSession) -> ImportJobRecord:
    job = await session.scalar(
        select(ImportJobRecord).where(
            ImportJobRecord.id == job_id, ImportJobRecord.owner_user_id == owner_id
        )
    )
    if job is None:
        raise HTTPException(status_code=404, detail="未找到导入任务")
    return job


@router.put("/imports/{job_id}/transcript", response_model=list[TranscriptSegment])
async def replace_transcript(
    job_id: UUID,
    payload: TranscriptReplace,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> list[TranscriptSegment]:
    await get_owned_import(job_id, owner.id, session)
    segments = sorted(payload.segments, key=lambda segment: segment.order)
    if any(segment.end_ms <= segment.start_ms for segment in segments):
        raise HTTPException(status_code=422, detail="字幕时间范围无效")
    if [segment.order for segment in segments] != list(range(len(segments))):
        raise HTTPException(status_code=422, detail="字幕顺序必须从 0 连续编号")
    await session.execute(
        delete(TranscriptSegmentRecord).where(TranscriptSegmentRecord.import_job_id == job_id)
    )
    session.add_all(
        TranscriptSegmentRecord(
            import_job_id=job_id,
            position=segment.order,
            start_ms=segment.start_ms,
            end_ms=segment.end_ms,
            text=segment.text,
            translation=segment.translation,
        )
        for segment in segments
    )
    await session.commit()
    return segments


@router.get("/imports/{job_id}/transcript", response_model=list[TranscriptSegment])
async def get_transcript(
    job_id: UUID,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> list[TranscriptSegment]:
    await get_owned_import(job_id, owner.id, session)
    rows = (
        await session.scalars(
            select(TranscriptSegmentRecord)
            .where(TranscriptSegmentRecord.import_job_id == job_id)
            .order_by(TranscriptSegmentRecord.position)
        )
    ).all()
    return [
        TranscriptSegment(
            id=row.id,
            start_ms=row.start_ms,
            end_ms=row.end_ms,
            text=row.text,
            translation=row.translation,
            order=row.position,
        )
        for row in rows
    ]


@router.post("/uploads", response_model=ImportJob, status_code=status.HTTP_202_ACCEPTED)
async def upload_media(
    request: Request,
    video: UploadFile = File(...),
    subtitle: UploadFile | None = File(default=None),
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> ImportJob:
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in VIDEO_SUFFIXES or not (video.content_type or "").startswith("video/"):
        raise HTTPException(status_code=422, detail="仅支持 MP4、WebM、MOV 或 M4V 视频上传")
    subtitle_segments: list[tuple[int, int, str]] = []
    if subtitle is not None:
        subtitle_suffix = Path(subtitle.filename or "").suffix.lower()
        if subtitle_suffix not in {".srt", ".vtt"}:
            raise HTTPException(status_code=422, detail="仅支持 SRT 或 VTT 字幕上传")
        raw_subtitle = await subtitle.read(10 * 1024 * 1024 + 1)
        if len(raw_subtitle) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="字幕文件超过大小限制")
        subtitle_segments = parse_subtitles(raw_subtitle.decode("utf-8", errors="strict"))
    settings = get_settings()
    root = Path(settings.media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4()}{suffix}"
    destination = safe_media_path(root, stored_name)
    limit = settings.max_upload_mb * 1024 * 1024
    try:
        declared_size = int(request.headers.get("content-length", "0"))
    except ValueError:
        declared_size = 0
    estimated_size = min(limit, declared_size) if declared_size > 0 else limit
    enforce_disk_budget(
        DiskBudget(
            free_bytes=shutil.disk_usage(root).free,
            estimated_media_bytes=max(1, estimated_size),
        )
    )
    total = 0
    try:
        with destination.open("xb") as target:
            while chunk := await video.read(64 * 1024):
                total += len(chunk)
                if total > limit:
                    raise HTTPException(status_code=413, detail="上传文件超过大小限制")
                target.write(chunk)
        validate_media_signature(destination, suffix)
        job = ImportJobRecord(owner_user_id=owner.id, source_url=f"upload://{stored_name}")
        session.add(job)
        await session.flush()
        session.add(
            MediaAsset(
                owner_user_id=owner.id,
                import_job_id=job.id,
                stored_name=stored_name,
                mime_type=video.content_type,
                size_bytes=total,
            )
        )
        session.add_all(
            TranscriptSegmentRecord(
                import_job_id=job.id,
                position=position,
                start_ms=start_ms,
                end_ms=end_ms,
                text=text,
            )
            for position, (start_ms, end_ms, text) in enumerate(subtitle_segments)
        )
        await session.commit()
        await session.refresh(job)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await video.close()
        if subtitle is not None:
            await subtitle.close()
    import_media.delay(str(job.id), request.headers.get("x-request-id"))
    return to_schema(job)


@router.get("/media/{asset_id}")
async def stream_media(
    asset_id: UUID,
    request: Request,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    asset = await session.scalar(
        select(MediaAsset).where(MediaAsset.id == asset_id, MediaAsset.owner_user_id == owner.id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="未找到媒体")
    path = safe_media_path(Path(get_settings().media_root).resolve(), asset.stored_name)
    if not path.is_file() or path.stat().st_size != asset.size_bytes:
        raise HTTPException(status_code=404, detail="媒体文件不可用")
    byte_range = parse_range(request.headers.get("range"), asset.size_bytes)
    start, end = byte_range or (0, asset.size_bytes - 1)
    headers = {"Accept-Ranges": "bytes", "Content-Length": str(end - start + 1)}
    if byte_range:
        headers["Content-Range"] = f"bytes {start}-{end}/{asset.size_bytes}"
    return StreamingResponse(
        iter_bytes(path, start, end),
        status_code=206 if byte_range else 200,
        media_type=asset.mime_type,
        headers=headers,
    )


@router.delete("/media/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    asset_id: UUID,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> Response:
    asset = await session.scalar(
        select(MediaAsset).where(MediaAsset.id == asset_id, MediaAsset.owner_user_id == owner.id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="未找到媒体")
    path = safe_media_path(Path(get_settings().media_root).resolve(), asset.stored_name)
    path.unlink(missing_ok=True)
    await session.delete(asset)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
