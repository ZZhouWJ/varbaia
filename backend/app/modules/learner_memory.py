"""Promotion rules for owner-controlled long-term learning memory."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LearnerMemoryItem

PROMOTION_THRESHOLD = 2


async def record_signal(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    category: str,
    memory_key: str,
    title: str,
    detail: str,
    source_type: str,
    severity: int = 1,
    force_active: bool = False,
) -> LearnerMemoryItem | None:
    """Promote recurring signals; a user-created signal may be promoted immediately."""
    item = await session.scalar(
        select(LearnerMemoryItem).where(
            LearnerMemoryItem.owner_user_id == owner_user_id,
            LearnerMemoryItem.category == category,
            LearnerMemoryItem.memory_key == memory_key,
        )
    )
    now = datetime.now(UTC)
    if item is None:
        item = LearnerMemoryItem(
            owner_user_id=owner_user_id,
            category=category,
            memory_key=memory_key,
            title=title,
            detail=detail,
            source_type=source_type,
            occurrence_count=1,
            severity=severity,
            status="active" if force_active else "observing",
            last_seen_at=now,
        )
        session.add(item)
    else:
        item.occurrence_count += 1
        item.severity = max(item.severity, severity)
        item.detail = detail
        item.last_seen_at = now
        if item.status == "mastered":
            item.status = "observing"
    if force_active or item.occurrence_count >= PROMOTION_THRESHOLD:
        item.status = "active"
    return item if item.status == "active" else None
