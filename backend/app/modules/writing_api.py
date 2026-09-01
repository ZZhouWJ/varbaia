from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import User, WritingAttempt
from app.modules.auth import get_owner

router = APIRouter(prefix="/owner/writing", tags=["owner-writing"])


class WritingSubmit(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    draft: str = Field(min_length=1, max_length=6000)


class WritingAttemptResponse(BaseModel):
    id: UUID
    prompt: str
    draft: str
    clarity_score: int | None


@router.post(
    "/attempts", response_model=WritingAttemptResponse, status_code=status.HTTP_202_ACCEPTED
)
async def submit_writing(
    payload: WritingSubmit,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> WritingAttemptResponse:
    attempt = WritingAttempt(owner_user_id=owner.id, prompt=payload.prompt, draft=payload.draft)
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return WritingAttemptResponse(
        id=attempt.id,
        prompt=attempt.prompt,
        draft=attempt.draft,
        clarity_score=attempt.clarity_score,
    )


@router.get("/attempts/{attempt_id}", response_model=WritingAttemptResponse)
async def get_writing_attempt(
    attempt_id: UUID,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> WritingAttemptResponse:
    attempt = await session.scalar(
        select(WritingAttempt).where(
            WritingAttempt.id == attempt_id, WritingAttempt.owner_user_id == owner.id
        )
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到写作记录")
    return WritingAttemptResponse(
        id=attempt.id,
        prompt=attempt.prompt,
        draft=attempt.draft,
        clarity_score=attempt.clarity_score,
    )
