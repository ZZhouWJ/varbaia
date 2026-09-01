import json
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse

from app.core.config import get_settings
from app.core.database import get_session
from app.models import RolePlayMessage, RolePlaySession, User
from app.modules.auth import get_owner
from app.modules.role_play_tasks import evaluate_role_play, reply_to_role_play
from app.providers.audio_normalization import normalize_audio
from app.providers.pronunciation import PronunciationProviderError
from app.providers.tencent_speech import TencentEnglishSpeechProvider

router = APIRouter(prefix="/owner/role-play", tags=["owner-role-play"])


class SessionCreate(BaseModel):
    scenario: str = Field(min_length=1, max_length=240)


class TurnCreate(BaseModel):
    learner_message: str = Field(min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    id: UUID
    speaker: str
    content: str
    coaching_tip: str | None
    audio_available: bool
    created_at: datetime


class SessionResponse(BaseModel):
    id: UUID
    scenario: str
    status: str
    messages: list[MessageResponse]
    feedback: dict[str, object] | None


async def get_owned_session(session_id: UUID, owner_id: UUID, db: AsyncSession) -> RolePlaySession:
    item = await db.scalar(
        select(RolePlaySession).where(
            RolePlaySession.id == session_id, RolePlaySession.owner_user_id == owner_id
        )
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到角色扮演会话")
    return item


async def to_response(item: RolePlaySession, db: AsyncSession) -> SessionResponse:
    messages = (
        await db.scalars(
            select(RolePlayMessage)
            .where(RolePlayMessage.session_id == item.id)
            .order_by(RolePlayMessage.created_at)
        )
    ).all()
    return SessionResponse(
        id=item.id,
        scenario=item.scenario,
        status=item.status,
        messages=[
            MessageResponse(
                id=message.id,
                speaker=message.speaker,
                content=message.content,
                coaching_tip=message.coaching_tip,
                audio_available=message.audio_stored_name is not None,
                created_at=message.created_at,
            )
            for message in messages
        ],
        feedback=json.loads(item.feedback_json) if item.feedback_json else None,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    item = RolePlaySession(owner_user_id=owner.id, scenario=payload.scenario)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return await to_response(item, db)


@router.post("/sessions/{session_id}/turns", response_model=SessionResponse, status_code=202)
async def add_learner_turn(
    session_id: UUID,
    payload: TurnCreate,
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    item = await get_owned_session(session_id, owner.id, db)
    db.add(RolePlayMessage(session_id=item.id, speaker="learner", content=payload.learner_message))
    item.status = "waiting_for_reply"
    await db.commit()
    reply_to_role_play.delay(str(item.id))
    return await to_response(item, db)


@router.post("/sessions/{session_id}/complete", response_model=SessionResponse, status_code=202)
async def complete_session(
    session_id: UUID,
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    item = await get_owned_session(session_id, owner.id, db)
    if item.status in {"complete", "evaluating"}:
        return await to_response(item, db)
    item.status = "evaluating"
    await db.commit()
    evaluate_role_play.delay(str(item.id))
    return await to_response(item, db)


@router.post("/sessions/{session_id}/voice-turns", response_model=SessionResponse, status_code=202)
async def add_voice_turn(
    session_id: UUID,
    audio: UploadFile = File(...),
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Use server-side Tencent ASR; browser clients never receive cloud secrets."""
    item = await get_owned_session(session_id, owner.id, db)
    suffix = Path(audio.filename or "recording.webm").suffix.lower()
    is_supported = suffix in {".webm", ".wav", ".ogg", ".mp4"}
    is_audio = (audio.content_type or "").startswith("audio/")
    if not is_supported or not is_audio:
        raise HTTPException(422, "仅支持 WebM、WAV、OGG 或 MP4 音频")
    raw = await audio.read(20 * 1024 * 1024 + 1)
    await audio.close()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "录音文件超过 20MB")
    settings = get_settings()
    temporary = Path(settings.media_root).resolve() / f"role-play-input-{uuid4()}{suffix}"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_bytes(raw)
    try:
        normalized = await normalize_audio(temporary, audio.content_type or "")
        speech_provider = TencentEnglishSpeechProvider(settings)
        transcript = await speech_provider.transcribe_pcm16(normalized.pcm_bytes)
    except PronunciationProviderError as exc:
        status_code = 422 if exc.category in {"invalid_audio", "invalid_reference_text"} else 503
        raise HTTPException(status_code, str(exc)) from exc
    finally:
        temporary.unlink(missing_ok=True)
    db.add(RolePlayMessage(session_id=item.id, speaker="learner", content=transcript))
    item.status = "waiting_for_reply"
    await db.commit()
    reply_to_role_play.delay(str(item.id))
    return await to_response(item, db)


@router.get("/sessions/{session_id}/messages/{message_id}/audio")
async def get_message_audio(
    session_id: UUID,
    message_id: UUID,
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> FileResponse:
    await get_owned_session(session_id, owner.id, db)
    message = await db.scalar(
        select(RolePlayMessage).where(
            RolePlayMessage.id == message_id, RolePlayMessage.session_id == session_id
        )
    )
    if message is None or not message.audio_stored_name or not message.audio_mime_type:
        raise HTTPException(404, "未找到角色扮演语音")
    path = Path(get_settings().media_root).resolve() / message.audio_stored_name
    if not path.is_file():
        raise HTTPException(404, "角色扮演语音已不可用")
    return FileResponse(path, media_type=message.audio_mime_type, filename="role-play-reply.wav")


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_role_play_session(
    session_id: UUID,
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    return await to_response(await get_owned_session(session_id, owner.id, db), db)
