from __future__ import annotations

import asyncio
import logging

from app.core.logging import configure_logging
from app.core.metrics import metrics
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.ml.anomaly import AnomalyService
from app.services.processor import ObservationProcessor
from app.services.queue import RedisQueue

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self) -> None:
        self.queue = RedisQueue()
        self.anomaly_service = AnomalyService()
        self.processor = ObservationProcessor(self.anomaly_service)
        self._running = True

    async def run(self) -> None:
        logger.info("worker started")
        while self._running:
            payload = await self.queue.dequeue(timeout_seconds=5)
            if payload is None:
                continue

            db = SessionLocal()
            try:
                self.processor.process(payload, db)
            except Exception:
                metrics.incr("worker_failed")
                logger.exception("worker failed to process payload")
            finally:
                db.close()

    async def stop(self) -> None:
        self._running = False
        await self.queue.close()


async def run_worker_forever() -> None:
    configure_logging()
    init_db()
    worker = Worker()
    try:
        await worker.run()
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(run_worker_forever())
