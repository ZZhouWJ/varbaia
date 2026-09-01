import json
import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import DictationAttempt, User
from app.modules.auth import get_owner

router = APIRouter(prefix="/owner/dictation", tags=["owner-dictation"])


class DictationSubmit(BaseModel):
    answer: str = Field(min_length=1, max_length=1000)
    reference: str = Field(min_length=1, max_length=1000)
    import_job_id: UUID | None = None
    segment_id: UUID | None = None


class DictationResult(BaseModel):
    id: UUID
    score: int
    missed_words: list[str]
    normalized_answer: str
    created_at: datetime


def score_dictation(answer: str, reference: str) -> tuple[int, list[str], str]:
    def normalize(value: str) -> list[str]:
        return re.findall(r"[a-z]+(?:'[a-z]+)?", value.lower())

    answer_words, reference_words = normalize(answer), normalize(reference)
    remaining = list(answer_words)
    missed = []
    for word in reference_words:
        if word in remaining:
            remaining.remove(word)
        else:
            missed.append(word)
    score = round(100 * (len(reference_words) - len(missed)) / max(len(reference_words), 1))
    return score, missed, " ".join(answer_words)


@router.post("/attempts", response_model=DictationResult, status_code=status.HTTP_201_CREATED)
async def submit_dictation(
    payload: DictationSubmit,
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> DictationResult:
    score, missed, normalized = score_dictation(payload.answer, payload.reference)
    attempt = DictationAttempt(
        owner_user_id=owner.id,
        import_job_id=payload.import_job_id,
        segment_id=payload.segment_id,
        answer=payload.answer,
        reference=payload.reference,
        score=score,
        missed_words_json=json.dumps(missed),
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    return DictationResult(
        id=attempt.id,
        score=attempt.score,
        missed_words=missed,
        normalized_answer=normalized,
        created_at=attempt.created_at,
    )
