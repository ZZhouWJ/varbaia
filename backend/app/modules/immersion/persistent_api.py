from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models import ImportJobRecord, User
from app.modules.auth import get_owner
from app.modules.immersion.schemas import ImportJob, VideoImportRequest
from app.modules.immersion.service import ImmersionService
from app.modules.immersion.tasks import import_media

router = APIRouter(prefix="/owner/immersion", tags=["owner-immersion"])


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
