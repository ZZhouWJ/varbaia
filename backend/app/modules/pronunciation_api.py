import json
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models import PronunciationAttempt, User
from app.modules.auth import get_owner
from app.modules.pronunciation_tasks import evaluate_pronunciation
from app.providers.audio_normalization import validate_reference_text
from app.providers.pronunciation import PronunciationProviderError

router = APIRouter(prefix="/owner/pronunciation", tags=["owner-pronunciation"])
SUFFIXES = {".webm", ".wav", ".ogg", ".mp4"}


class AttemptResponse(BaseModel):
    id: UUID
    reference_text: str
    evaluation_status: str
    result: dict[str, object] | None
    evaluation_error: str | None


def response_of(attempt: PronunciationAttempt) -> AttemptResponse:
    return AttemptResponse(
        id=attempt.id,
        reference_text=attempt.reference_text,
        evaluation_status=attempt.evaluation_status,
        result=json.loads(attempt.result_json) if attempt.result_json else None,
        evaluation_error=attempt.evaluation_error,
    )


@router.post("/attempts", response_model=AttemptResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_attempt(
    reference_text: str = Form(...),
    audio: UploadFile = File(...),
    owner: User = Depends(get_owner),
    session: AsyncSession = Depends(get_session),
) -> AttemptResponse:
    try:
        normalized_reference_text = validate_reference_text(reference_text)
    except PronunciationProviderError as exc:
        raise HTTPException(422, str(exc)) from exc
    suffix = Path(audio.filename or "").suffix.lower()
    if suffix not in SUFFIXES or not (audio.content_type or "").startswith("audio/"):
        raise HTTPException(422, "仅支持 WebM、WAV、OGG 或 MP4 音频")
    raw = await audio.read(20 * 1024 * 1024 + 1)
    await audio.close()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "录音文件超过 20MB")
    root = Path(get_settings().media_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4()}{suffix}"
    (root / name).write_bytes(raw)
    attempt = PronunciationAttempt(
        owner_user_id=owner.id,
        reference_text=normalized_reference_text,
        stored_name=name,
        mime_type=audio.content_type,
    )
    session.add(attempt)
    await session.commit()
    await session.refresh(attempt)
    evaluate_pronunciation.delay(str(attempt.id))
    return response_of(attempt)


@router.get("/attempts/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: UUID, owner: User = Depends(get_owner), session: AsyncSession = Depends(get_session)
) -> AttemptResponse:
    attempt = await session.scalar(
        select(PronunciationAttempt).where(
            PronunciationAttempt.id == attempt_id, PronunciationAttempt.owner_user_id == owner.id
        )
    )
    if attempt is None:
        raise HTTPException(404, "未找到跟读记录")
    return response_of(attempt)
