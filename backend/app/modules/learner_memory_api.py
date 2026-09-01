from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import LearnerMemoryItem, User
from app.modules.auth import get_owner
from app.modules.learner_memory import record_signal

router = APIRouter(prefix="/owner/memory", tags=["owner-memory"])
MemoryCategory = Literal[
    "pronunciation", "listening", "vocabulary", "grammar", "fluency", "writing"
]


class MemoryCreate(BaseModel):
    category: MemoryCategory
    title: str = Field(min_length=1, max_length=240)
    detail: str = Field(min_length=1, max_length=2000)


class MemoryResponse(BaseModel):
    id: UUID
    category: MemoryCategory
    title: str
    detail: str
    source_type: str
    occurrence_count: int
    severity: int
    status: str
    last_seen_at: datetime


@router.get("", response_model=list[MemoryResponse])
async def list_memory(
    owner: User = Depends(get_owner), session: AsyncSession = Depends(get_session)
) -> list[MemoryResponse]:
    items = (
        await session.scalars(
            select(LearnerMemoryItem)
            .where(
                LearnerMemoryItem.owner_user_id == owner.id,
                LearnerMemoryItem.status == "active",
            )
            .order_by(LearnerMemoryItem.severity.desc(), LearnerMemoryItem.last_seen_at.desc())
        )
    ).all()
    return [MemoryResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(
    payload: MemoryCreate,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> MemoryResponse:
    item = await record_signal(
        session,
        owner_user_id=owner.id,
        category=payload.category,
        memory_key=payload.title.strip().lower()[:160],
        title=payload.title.strip(),
        detail=payload.detail.strip(),
        source_type="owner",
        force_active=True,
    )
    assert item is not None
    await session.commit()
    await session.refresh(item)
    return MemoryResponse.model_validate(item, from_attributes=True)


@router.post("/{memory_id}/master", response_model=MemoryResponse)
async def mark_mastered(
    memory_id: UUID, owner: User = Depends(get_owner), session: AsyncSession = Depends(get_session)
) -> MemoryResponse:
    item = await session.scalar(
        select(LearnerMemoryItem).where(
            LearnerMemoryItem.id == memory_id, LearnerMemoryItem.owner_user_id == owner.id
        )
    )
    if item is None:
        raise HTTPException(404, "未找到学习记忆")
    item.status = "mastered"
    await session.commit()
    await session.refresh(item)
    return MemoryResponse.model_validate(item, from_attributes=True)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: UUID, owner: User = Depends(get_owner), session: AsyncSession = Depends(get_session)
) -> None:
    item = await session.scalar(
        select(LearnerMemoryItem).where(
            LearnerMemoryItem.id == memory_id, LearnerMemoryItem.owner_user_id == owner.id
        )
    )
    if item is None:
        raise HTTPException(404, "未找到学习记忆")
    await session.delete(item)
    await session.commit()
