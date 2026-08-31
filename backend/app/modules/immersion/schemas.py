from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ImportStatus(StrEnum):
    queued = "queued"
    fetching = "fetching"
    transcribing = "transcribing"
    segmenting = "segmenting"
    ready = "ready"
    failed = "failed"


class VideoImportRequest(BaseModel):
    source_url: HttpUrl
    accent: str = Field(default="en-US", pattern=r"^en-(US|GB)$")
    title_hint: str | None = Field(default=None, max_length=180)

    @field_validator("source_url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("仅接受 HTTPS 视频地址")
        return value


class ImportJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_url: HttpUrl
    status: ImportStatus = ImportStatus.queued
    progress: int = Field(default=0, ge=0, le=100)
    message: str = "已进入处理队列"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TranscriptSegment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=800)
    translation: str | None = Field(default=None, max_length=1200)
    order: int = Field(ge=0)


class DictationSubmit(BaseModel):
    segment_id: UUID
    answer: str = Field(min_length=1, max_length=1000)
    reference: str = Field(min_length=1, max_length=1000)


class DictationResult(BaseModel):
    score: int = Field(ge=0, le=100)
    missed_words: list[str]
    normalized_answer: str


class WritingFeedbackRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    draft: str = Field(min_length=1, max_length=6000)


class WritingFeedback(BaseModel):
    clarity_score: int = Field(ge=0, le=100)
    corrected_draft: str
    suggestions: list[str]


class RolePlayTurn(BaseModel):
    scenario: str = Field(min_length=1, max_length=120)
    learner_message: str = Field(min_length=1, max_length=1000)


class RolePlayReply(BaseModel):
    reply: str
    coaching_tip: str
