import re
from collections import defaultdict
from urllib.parse import urlparse
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import Settings
from app.modules.immersion.schemas import (
    DictationResult,
    ImportJob,
    ImportStatus,
    RolePlayReply,
    TranscriptSegment,
    VideoImportRequest,
    WritingFeedback,
    WritingFeedbackRequest,
)


class ImmersionService:
    """In-memory development adapter; replace with repository + Celery task in production."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.jobs: dict[UUID, ImportJob] = {}
        self.segments: dict[UUID, list[TranscriptSegment]] = defaultdict(list)

    def create_import(self, payload: VideoImportRequest) -> ImportJob:
        hostname = (urlparse(str(payload.source_url)).hostname or "").lower()
        is_allowed = any(
            hostname == host or hostname.endswith(f".{host}")
            for host in self.settings.allowed_media_hosts
        )
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="该视频来源不在允许列表中",
            )
        job = ImportJob(source_url=payload.source_url)
        self.jobs[job.id] = job
        return job

    def advance_import(self, job_id: UUID) -> ImportJob:
        job = self.get_job(job_id)
        states = [
            (ImportStatus.fetching, 18, "正在读取视频元数据"),
            (ImportStatus.transcribing, 58, "正在请求英语转写服务"),
            (ImportStatus.segmenting, 86, "正在生成可练习片段"),
            (ImportStatus.ready, 100, "学习材料已就绪"),
        ]
        current_index = next((i for i, item in enumerate(states) if item[0] == job.status), -1)
        next_status, progress, message = states[min(current_index + 1, len(states) - 1)]
        updated = job.model_copy(
            update={"status": next_status, "progress": progress, "message": message}
        )
        self.jobs[job_id] = updated
        return updated

    def get_job(self, job_id: UUID) -> ImportJob:
        job = self.jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到导入任务")
        return job

    def submit_dictation(self, answer: str, reference: str) -> DictationResult:
        def normalize(value: str) -> list[str]:
            return re.findall(r"[a-z]+(?:'[a-z]+)?", value.lower())

        answer_words, reference_words = normalize(answer), normalize(reference)
        remaining = list(answer_words)
        missed: list[str] = []
        for word in reference_words:
            if word in remaining:
                remaining.remove(word)
            else:
                missed.append(word)
        score = round(100 * (len(reference_words) - len(missed)) / max(len(reference_words), 1))
        return DictationResult(
            score=score,
            missed_words=missed,
            normalized_answer=" ".join(answer_words),
        )

    def give_writing_feedback(self, payload: WritingFeedbackRequest) -> WritingFeedback:
        sentences = [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+", payload.draft)
            if item.strip()
        ]
        corrected = " ".join(sentence[:1].upper() + sentence[1:] for sentence in sentences)
        suggestions = ["先用一句话回答题目，再补充一个具体例子。"]
        if len(payload.draft.split()) < 45:
            suggestions.append("尝试加入一个原因与一个结果，让段落更完整。")
        else:
            suggestions.append("检查连接词是否清楚地表达了句子之间的关系。")
        return WritingFeedback(
            clarity_score=min(94, 62 + len(sentences) * 8),
            corrected_draft=corrected,
            suggestions=suggestions,
        )

    def reply_to_role_play(self, scenario: str, learner_message: str) -> RolePlayReply:
        reply = (
            f"That sounds reasonable. In this {scenario.lower()} situation, "
            "could you tell me one more detail?"
        )
        tip = "很好：保持句子简短。下一句可尝试使用一个追问，例如 “Could you tell me…?”"
        return RolePlayReply(reply=reply, coaching_tip=tip)
