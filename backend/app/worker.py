"""Celery worker module entrypoint for local process managers."""

from app.core.tasks import celery_app


def main() -> None:
    celery_app.worker_main(["worker", "--loglevel=info", "--concurrency=1"])


if __name__ == "__main__":
    main()
