import logging
from time import perf_counter

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import get_settings
from app.core.observability import configure_logging, request_id_from
from app.modules.auth import router as auth_router
from app.modules.dictation_api import router as dictation_router
from app.modules.immersion.persistent_api import router as persistent_immersion_router
from app.modules.learner_memory_api import router as learner_memory_router
from app.modules.progress_api import router as progress_router
from app.modules.pronunciation_api import router as pronunciation_router
from app.modules.role_play_api import router as role_play_router
from app.modules.vocabulary_api import router as vocabulary_router
from app.modules.writing_api import router as writing_router


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(router)
    app.include_router(auth_router, prefix="/api")
    app.include_router(dictation_router, prefix="/api")
    app.include_router(persistent_immersion_router, prefix="/api")
    app.include_router(writing_router, prefix="/api")
    app.include_router(vocabulary_router, prefix="/api")
    app.include_router(progress_router, prefix="/api")
    app.include_router(learner_memory_router, prefix="/api")
    app.include_router(pronunciation_router, prefix="/api")
    app.include_router(role_play_router, prefix="/api")

    @app.middleware("http")
    async def add_request_context(request: Request, call_next: object) -> Response:
        request_id = request_id_from(request.headers.get("x-request-id"))
        request.state.request_id = request_id
        started_at = perf_counter()
        try:
            response = await call_next(request)  # type: ignore[operator]
        except Exception:
            logging.getLogger("varbaia.request").exception(
                "request_failed",
                extra={
                    "fields": {
                        "request_id": request_id,
                        "route": request.url.path,
                        "latency_ms": round((perf_counter() - started_at) * 1000),
                    }
                },
            )
            raise
        response.headers["X-Request-ID"] = request_id
        logging.getLogger("varbaia.request").info(
            "request_complete",
            extra={
                "fields": {
                    "request_id": request_id,
                    "route": getattr(request.scope.get("route"), "path", request.url.path),
                    "status": response.status_code,
                    "latency_ms": round((perf_counter() - started_at) * 1000),
                }
            },
        )
        return response

    return app


app = create_app()
