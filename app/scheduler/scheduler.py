from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.metrics import metrics
from app.schemas.observation import ObservationIn
from app.services.adapters import AirQualityAdapter, WeatherAdapter
from app.services.queue import RedisQueue

settings = get_settings()
logger = logging.getLogger(__name__)


class ProducerScheduler:
    def __init__(self) -> None:
        self.queue = RedisQueue()
        self.weather_adapter = WeatherAdapter()
        self.aq_adapter = AirQualityAdapter()
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    async def _publish_observation(self, observation: ObservationIn) -> None:
        await self.queue.enqueue(observation.model_dump(mode="json", by_alias=True))
        metrics.incr("jobs_enqueued")

    async def collect_once(self) -> None:
        lat = settings.default_latitude
        lon = settings.default_longitude
        location = settings.default_location_name

        results = await asyncio.gather(
            self.weather_adapter.fetch(lat, lon, location),
            self.aq_adapter.fetch(lat, lon, location),
            return_exceptions=True,
        )

        success = 0
        for result in results:
            if isinstance(result, Exception):
                metrics.incr("producer_source_failed")
                logger.exception("source collection failed", exc_info=result)
                continue
            await self._publish_observation(result)
            success += 1

        if success == 0:
            metrics.incr("producer_round_failed")
        else:
            metrics.incr("producer_round_success")
        logger.info("producer round complete success=%s", success)

    def start(self) -> None:
        self.scheduler.add_job(self.collect_once, "interval", seconds=settings.scheduler_interval_seconds, max_instances=1)
        self.scheduler.start()
        logger.info("scheduler started interval=%s", settings.scheduler_interval_seconds)

    async def stop(self) -> None:
        self.scheduler.shutdown(wait=False)
        await self.queue.close()


async def run_scheduler_forever() -> None:
    runner = ProducerScheduler()
    runner.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.stop()
