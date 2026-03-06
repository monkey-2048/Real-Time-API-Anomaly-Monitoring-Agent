from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone

import httpx

from app.core.config import get_settings
from app.core.metrics import metrics
from app.schemas.observation import ObservationIn
from app.services.normalizer import normalize_air_quality_payload, normalize_weather_payload
from app.utils.retries import retry_async

logger = logging.getLogger(__name__)
settings = get_settings()


class WeatherAdapter:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def fetch(self, latitude: float, longitude: float, location: str) -> ObservationIn:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "UTC",
        }

        async def _request() -> ObservationIn:
            started = time.perf_counter()
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                payload = resp.json()
            latency_ms = (time.perf_counter() - started) * 1000.0
            metrics.observe_ms("weather_api_latency", latency_ms)
            metrics.incr("weather_api_success")
            return normalize_weather_payload(payload, location=location, latency_ms=latency_ms)

        try:
            return await retry_async(_request, attempts=settings.http_retry_attempts)
        except Exception:
            metrics.incr("weather_api_failed")
            logger.exception("weather adapter failed")
            raise


class AirQualityAdapter:
    BASE_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    async def fetch(self, latitude: float, longitude: float, location: str) -> ObservationIn:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "pm2_5,pm10,us_aqi",
            "timezone": "UTC",
        }

        async def _request() -> ObservationIn:
            started = time.perf_counter()
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                resp = await client.get(self.BASE_URL, params=params)
                resp.raise_for_status()
                payload = resp.json()
            latency_ms = (time.perf_counter() - started) * 1000.0
            metrics.observe_ms("air_quality_api_latency", latency_ms)
            metrics.incr("air_quality_api_success")
            return normalize_air_quality_payload(payload, location=location, latency_ms=latency_ms)

        try:
            return await retry_async(_request, attempts=settings.http_retry_attempts)
        except Exception:
            metrics.incr("air_quality_api_failed")
            logger.warning("public air-quality API failed; falling back to mock adapter")
            return await MockAirQualityAdapter().fetch(latitude=latitude, longitude=longitude, location=location)


class MockAirQualityAdapter:
    async def fetch(self, latitude: float, longitude: float, location: str) -> ObservationIn:
        await asyncio.sleep(0.05)
        now = datetime.now(timezone.utc)
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "current": {
                "time": now.isoformat(),
                "pm2_5": round(random.uniform(5, 60), 2),
                "pm10": round(random.uniform(10, 80), 2),
                "us_aqi": round(random.uniform(25, 140), 2),
            },
        }
        metrics.incr("air_quality_mock_used")
        return normalize_air_quality_payload(payload, location=location, latency_ms=50.0)
