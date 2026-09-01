from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import ProgressRecord, User
from app.modules.auth import get_owner

router = APIRouter(prefix="/owner/progress", tags=["owner-progress"])


class ProgressUpsert(BaseModel):
    resource_type: str = Field(min_length=1, max_length=40, pattern=r"^[a-z_]+$")
    resource_id: UUID
    completion_percent: int = Field(ge=0, le=100)
    last_position_seconds: int = Field(ge=0, le=86_400)


class ProgressResponse(ProgressUpsert):
    id: UUID
    updated_at: datetime


def to_response(record: ProgressRecord) -> ProgressResponse:
    return ProgressResponse.model_validate(record, from_attributes=True)


@router.put("", response_model=ProgressResponse)
async def save_progress(
    payload: ProgressUpsert,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> ProgressResponse:
    record = await session.scalar(
        select(ProgressRecord).where(
            ProgressRecord.owner_user_id == owner.id,
            ProgressRecord.resource_type == payload.resource_type,
            ProgressRecord.resource_id == payload.resource_id,
        )
    )
    if record is None:
        record = ProgressRecord(owner_user_id=owner.id, **payload.model_dump())
        session.add(record)
    else:
        record.completion_percent = payload.completion_percent
        record.last_position_seconds = payload.last_position_seconds
        record.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(record)
    return to_response(record)


@router.get("/{resource_type}/{resource_id}", response_model=ProgressResponse)
async def get_progress(
    resource_type: str,
    resource_id: UUID,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> ProgressResponse:
    record = await session.scalar(
        select(ProgressRecord).where(
            ProgressRecord.owner_user_id == owner.id,
            ProgressRecord.resource_type == resource_type,
            ProgressRecord.resource_id == resource_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到学习进度")
    return to_response(record)
