from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import User, VocabularyItem
from app.modules.auth import get_owner

router = APIRouter(prefix="/owner/vocabulary", tags=["owner-vocabulary"])


class VocabularyCreate(BaseModel):
    term: str = Field(min_length=1, max_length=160)
    definition: str = Field(min_length=1, max_length=1000)


class VocabularyResponse(BaseModel):
    id: UUID
    term: str
    definition: str
    interval_days: int
    repetitions: int
    next_review_at: datetime


@router.post("/items", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
async def create_vocabulary_item(
    payload: VocabularyCreate,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> VocabularyResponse:
    item = VocabularyItem(owner_user_id=owner.id, term=payload.term, definition=payload.definition)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return VocabularyResponse.model_validate(item, from_attributes=True)


@router.get("/due", response_model=list[VocabularyResponse])
async def list_due_vocabulary(
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> list[VocabularyResponse]:
    items = (
        await session.scalars(
            select(VocabularyItem).where(
                VocabularyItem.owner_user_id == owner.id,
                VocabularyItem.next_review_at <= datetime.now(UTC),
            )
        )
    ).all()
    return [VocabularyResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("/items/{item_id}/review/{grade}", response_model=VocabularyResponse)
async def review_vocabulary(
    item_id: UUID,
    grade: str,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> VocabularyResponse:
    item = await session.scalar(
        select(VocabularyItem).where(
            VocabularyItem.id == item_id, VocabularyItem.owner_user_id == owner.id
        )
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到词汇")
    if grade not in {"again", "hard", "good", "easy"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="无效复习等级"
        )
    item.repetitions = 0 if grade == "again" else item.repetitions + 1
    item.interval_days = (
        1 if grade == "again" else max(1, item.interval_days * (2 if grade == "easy" else 1))
    )
    item.next_review_at = datetime.now(UTC) + timedelta(days=item.interval_days)
    await session.commit()
    await session.refresh(item)
    return VocabularyResponse.model_validate(item, from_attributes=True)
