from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core.config import get_settings
from app.modules.auth import router as auth_router
from app.modules.immersion.persistent_api import router as persistent_immersion_router
from app.modules.vocabulary_api import router as vocabulary_router
from app.modules.writing_api import router as writing_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    app.include_router(router)
    app.include_router(auth_router, prefix="/api")
    app.include_router(persistent_immersion_router, prefix="/api")
    app.include_router(writing_router, prefix="/api")
    app.include_router(vocabulary_router, prefix="/api")
    return app


app = create_app()
