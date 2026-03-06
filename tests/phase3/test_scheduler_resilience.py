from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.metrics import metrics
from app.scheduler.scheduler import ProducerScheduler
from app.schemas.observation import ObservationIn


class FakeQueue:
    def __init__(self) -> None:
        self.items: list[dict] = []

    async def enqueue(self, payload: dict) -> None:
        self.items.append(payload)

    async def close(self) -> None:
        return None


class GoodAdapter:
    async def fetch(self, latitude: float, longitude: float, location: str) -> ObservationIn:
        return ObservationIn(
            source="weather",
            location=location,
            observed_at=datetime(2026, 3, 6, 0, 0, tzinfo=timezone.utc),
            latitude=latitude,
            longitude=longitude,
            temperature=25.0,
            humidity=60.0,
            wind_speed=3.0,
            source_latency_ms=30.0,
        )


class BadAdapter:
    async def fetch(self, latitude: float, longitude: float, location: str):
        raise RuntimeError("source failure")


def test_producer_collect_once_partial_failure_still_enqueues_one():
    runner = ProducerScheduler()
    fake_queue = FakeQueue()

    runner.queue = fake_queue
    runner.weather_adapter = GoodAdapter()
    runner.aq_adapter = BadAdapter()

    before = metrics.snapshot()
    before_jobs = before["counters"].get("jobs_enqueued", 0)

    asyncio.run(runner.collect_once())

    after = metrics.snapshot()
    after_jobs = after["counters"].get("jobs_enqueued", 0)

    assert len(fake_queue.items) == 1
    assert after_jobs == before_jobs + 1


def test_producer_collect_once_all_failure_marks_round_failed():
    runner = ProducerScheduler()
    fake_queue = FakeQueue()

    runner.queue = fake_queue
    runner.weather_adapter = BadAdapter()
    runner.aq_adapter = BadAdapter()

    before = metrics.snapshot()
    before_failed = before["counters"].get("producer_round_failed", 0)

    asyncio.run(runner.collect_once())

    after = metrics.snapshot()
    after_failed = after["counters"].get("producer_round_failed", 0)

    assert len(fake_queue.items) == 0
    assert after_failed == before_failed + 1
