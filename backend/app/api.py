from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.core.config import Settings, get_settings
from app.core.database import engine

router = APIRouter(prefix="/api")


@router.get("/health", tags=["system"])
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.app_env}


@router.get("/health/live", tags=["system"])
def live_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", tags=["system"])
async def ready_health() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="数据库尚未就绪") from exc
    return {"status": "ok", "database": "ready"}

