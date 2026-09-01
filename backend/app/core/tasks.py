from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "varbaia",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.modules.immersion.tasks", "app.modules.writing_tasks"],
)
celery_app.conf.update(
    task_default_queue="default",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=600,
    task_time_limit=660,
    task_track_started=True,
)
