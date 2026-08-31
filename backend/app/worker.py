"""Worker process entrypoint.

Production deployments replace this lightweight health-preserving loop with the
configured Celery task runner once the PostgreSQL/Redis repositories are enabled.
Keeping a dedicated process now reserves the asynchronous media-processing
boundary without coupling the HTTP process to long-running video work.
"""

import logging
import signal
from threading import Event

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
stop_requested = Event()


def request_stop(*_args: object) -> None:
    stop_requested.set()


def main() -> None:
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    logging.info("Verbaia worker ready; awaiting asynchronous media jobs")
    stop_requested.wait()
    logging.info("Verbaia worker stopped")


if __name__ == "__main__":
    main()
