from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.config import Settings, get_settings
from app.modules.immersion.schemas import (
    DictationResult,
    DictationSubmit,
    ImportJob,
    RolePlayReply,
    RolePlayTurn,
    VideoImportRequest,
    WritingFeedback,
    WritingFeedbackRequest,
)
from app.modules.immersion.service import ImmersionService

router = APIRouter(prefix="/api")
_services: dict[str, ImmersionService] = {}


def get_service(settings: Settings = Depends(get_settings)) -> ImmersionService:
    return _services.setdefault(settings.app_env, ImmersionService(settings))


@router.get("/health", tags=["system"])
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@router.post(
    "/immersion/imports", response_model=ImportJob, status_code=202, tags=["immersion"]
)
def create_import(
    payload: VideoImportRequest, service: ImmersionService = Depends(get_service)
) -> ImportJob:
    return service.create_import(payload)


@router.get("/immersion/imports/{job_id}", response_model=ImportJob, tags=["immersion"])
def get_import(
    job_id: UUID, service: ImmersionService = Depends(get_service)
) -> ImportJob:
    return service.get_job(job_id)


@router.post("/immersion/imports/{job_id}/advance", response_model=ImportJob, tags=["immersion"])
def advance_import(
    job_id: UUID, service: ImmersionService = Depends(get_service)
) -> ImportJob:
    return service.advance_import(job_id)


@router.get("/immersion/imports/{job_id}/events", tags=["immersion"])
async def import_events(
    job_id: UUID, service: ImmersionService = Depends(get_service)
) -> StreamingResponse:
    async def stream() -> AsyncIterator[str]:
        for _ in range(4):
            job = service.advance_import(job_id)
            yield f"event: progress\\ndata: {job.model_dump_json()}\\n\\n"
            if job.progress == 100:
                break
    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/practice/dictation", response_model=DictationResult, tags=["practice"])
def submit_dictation(
    payload: DictationSubmit, service: ImmersionService = Depends(get_service)
) -> DictationResult:
    return service.submit_dictation(answer=payload.answer, reference=payload.reference)


@router.post("/practice/writing-feedback", response_model=WritingFeedback, tags=["practice"])
def writing_feedback(
    payload: WritingFeedbackRequest, service: ImmersionService = Depends(get_service)
) -> WritingFeedback:
    return service.give_writing_feedback(payload)


@router.post("/practice/role-play", response_model=RolePlayReply, tags=["practice"])
def role_play(
    payload: RolePlayTurn, service: ImmersionService = Depends(get_service)
) -> RolePlayReply:
    return service.reply_to_role_play(payload.scenario, payload.learner_message)
