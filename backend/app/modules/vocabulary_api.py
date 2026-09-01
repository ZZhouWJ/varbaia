from datetime import UTC, datetime, timedelta
from math import floor
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
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
    ease: float
    repetitions: int
    next_review_at: datetime

    @field_validator("ease", mode="before")
    @classmethod
    def convert_ease_from_percentage(cls, value: int) -> float:
        return value / 100


ReviewGrade = Literal["again", "hard", "good", "easy"]


def schedule_review(item: VocabularyItem, grade: ReviewGrade) -> None:
    """Mirror frontend/lib/review.ts while storing ease as an integer percentage."""
    current_ease = item.ease / 100
    if grade == "again":
        item.interval_days = 1
        item.ease = floor(max(1.3, current_ease - 0.2) * 100 + 0.5)
        item.repetitions = 0
        return

    multiplier = 1.3 if grade == "easy" else 0.75 if grade == "hard" else 1
    next_ease = (
        current_ease + 0.15
        if grade == "easy"
        else max(1.3, current_ease - 0.15)
        if grade == "hard"
        else current_ease
    )
    base = (
        1
        if item.repetitions == 0
        else 3
        if item.repetitions == 1
        else item.interval_days * next_ease
    )
    item.interval_days = max(1, floor(base * multiplier + 0.5))
    item.ease = floor(next_ease * 100 + 0.5)
    item.repetitions += 1


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
    grade: ReviewGrade,
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
    schedule_review(item, grade)
    item.next_review_at = datetime.now(UTC) + timedelta(days=item.interval_days)
    await session.commit()
    await session.refresh(item)
    return VocabularyResponse.model_validate(item, from_attributes=True)
