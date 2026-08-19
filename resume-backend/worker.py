from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config import load_settings
from app.services.worker import BackgroundWorker


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()
    if not settings.worker_enabled:
        logger.info("worker disabled by WORKER_ENABLED")
        return

    worker = BackgroundWorker.from_settings(settings)
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        worker.run_all_once,
        "interval",
        seconds=settings.worker_scan_interval_seconds,
        id="phase9-maintenance",
        max_instances=1,
        coalesce=True,
    )
    logger.info("worker started with scan interval %s seconds", settings.worker_scan_interval_seconds)
    scheduler.start()


if __name__ == "__main__":
    main()
