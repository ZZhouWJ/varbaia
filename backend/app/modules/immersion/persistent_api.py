from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models import ImportJobRecord, MediaAsset, User
from app.modules.auth import get_owner
from app.modules.immersion.media import iter_bytes, parse_range, safe_media_path
from app.modules.immersion.schemas import ImportJob, VideoImportRequest
from app.modules.immersion.service import ImmersionService
from app.modules.immersion.tasks import import_media

router = APIRouter(prefix="/owner/immersion", tags=["owner-immersion"])
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v"}


def to_schema(record: ImportJobRecord) -> ImportJob:
    return ImportJob(
        id=record.id,
        source_url=record.source_url,
        status=record.status,
        progress=record.progress,
        message="任务处理中" if record.status != "ready" else "学习材料已就绪",
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


@router.post("/uploads", response_model=ImportJob, status_code=status.HTTP_202_ACCEPTED)
async def upload_media(
    request: Request,
    video: UploadFile = File(...),
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> ImportJob:
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in VIDEO_SUFFIXES or not (video.content_type or "").startswith("video/"):
        raise HTTPException(status_code=422, detail="仅支持 MP4、WebM、MOV 或 M4V 视频上传")
    settings = get_settings()
    root = Path(settings.media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4()}{suffix}"
    destination = safe_media_path(root, stored_name)
    limit = settings.max_upload_mb * 1024 * 1024
    total = 0
    try:
        with destination.open("xb") as target:
            while chunk := await video.read(64 * 1024):
                total += len(chunk)
                if total > limit:
                    raise HTTPException(status_code=413, detail="上传文件超过大小限制")
                target.write(chunk)
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
        await session.commit()
        await session.refresh(job)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await video.close()
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
