from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models import RolePlayMessage, RolePlaySession, User
from app.modules.auth import get_owner
from app.modules.role_play_tasks import reply_to_role_play

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
    created_at: datetime


class SessionResponse(BaseModel):
    id: UUID
    scenario: str
    status: str
    messages: list[MessageResponse]


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
            MessageResponse.model_validate(message, from_attributes=True) for message in messages
        ],
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


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    owner: User = Depends(get_owner),
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    return await to_response(await get_owned_session(session_id, owner.id, db), db)
