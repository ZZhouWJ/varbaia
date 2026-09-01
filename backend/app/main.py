import logging
from time import perf_counter

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool = False,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": getattr(request.state, "request_id", None),
                "retryable": retryable,
                "details": None,
            }
        },
    )


def http_error_code(status_code: int) -> str:
    return {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_401_UNAUTHORIZED: "AUTH_REQUIRED",
        status.HTTP_403_FORBIDDEN: "ACCESS_DENIED",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_409_CONFLICT: "CONFLICT",
        status.HTTP_413_CONTENT_TOO_LARGE: "PAYLOAD_TOO_LARGE",
        status.HTTP_422_UNPROCESSABLE_CONTENT: "VALIDATION_ERROR",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }.get(status_code, "REQUEST_FAILED")


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

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "请求未能完成。"
        return error_response(
            request,
            status_code=exc.status_code,
            code=http_error_code(exc.status_code),
            message=message,
            retryable=exc.status_code in {status.HTTP_429_TOO_MANY_REQUESTS, 503},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message="请求参数无效，请检查后重试。",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, _exc: Exception) -> JSONResponse:
        logging.getLogger("varbaia.error").exception(
            "unhandled_request_error",
            extra={"fields": {"request_id": getattr(request.state, "request_id", None)}},
        )
        return error_response(
            request,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="服务暂时不可用，请稍后重试。",
            retryable=True,
        )
    app.include_router(router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(dictation_router, prefix="/api/v1")
    app.include_router(persistent_immersion_router, prefix="/api/v1")
    app.include_router(writing_router, prefix="/api/v1")
    app.include_router(vocabulary_router, prefix="/api/v1")
    app.include_router(progress_router, prefix="/api/v1")
    app.include_router(learner_memory_router, prefix="/api/v1")
    app.include_router(pronunciation_router, prefix="/api/v1")
    app.include_router(role_play_router, prefix="/api/v1")

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
