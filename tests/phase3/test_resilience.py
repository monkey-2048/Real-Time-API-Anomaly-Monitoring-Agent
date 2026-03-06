from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx

from app.schemas.observation import ObservationIn
from app.services.adapters import AirQualityAdapter, MockAirQualityAdapter
from app.utils.retries import retry_async


def test_retry_async_retries_then_succeeds():
    state = {"count": 0}

    async def flaky_call() -> str:
        state["count"] += 1
        if state["count"] < 3:
            raise RuntimeError("temporary failure")
        return "ok"

    result = asyncio.run(retry_async(flaky_call, attempts=3, base_delay=0.01))
    assert result == "ok"
    assert state["count"] == 3


def test_air_quality_adapter_fallback_to_mock(monkeypatch):
    async def always_fail(*args, **kwargs):
        raise httpx.ConnectError("network down")

    async def fake_mock_fetch(self, latitude: float, longitude: float, location: str) -> ObservationIn:
        return ObservationIn(
            source="air_quality",
            location=location,
            observed_at=datetime(2026, 3, 6, 0, 0, tzinfo=timezone.utc),
            latitude=latitude,
            longitude=longitude,
            pm2_5=12.3,
            pm10=22.1,
            aqi=35.0,
            source_latency_ms=50.0,
        )

    monkeypatch.setattr("app.services.adapters.retry_async", always_fail)
    monkeypatch.setattr(MockAirQualityAdapter, "fetch", fake_mock_fetch)

    adapter = AirQualityAdapter()
    obs = asyncio.run(adapter.fetch(25.03, 121.56, "taipei"))

    assert obs.source == "air_quality"
    assert obs.location == "taipei"
    assert obs.pm25 == 12.3
    assert obs.pm10 == 22.1
    assert obs.aqi == 35.0
