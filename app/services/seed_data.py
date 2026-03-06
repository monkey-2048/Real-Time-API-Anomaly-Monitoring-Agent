from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.observation import ObservationProcessResult


def build_seed_observations(location: str = "taipei", n: int = 24) -> list[ObservationProcessResult]:
    base = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)
    rows: list[ObservationProcessResult] = []

    for i in range(n):
        ts = base + timedelta(hours=i)

        rows.append(
            ObservationProcessResult(
                source="weather",
                location=location,
                observed_at=ts,
                latitude=25.03,
                longitude=121.56,
                temperature=24.0 + (i % 6),
                humidity=58.0 + (i % 10),
                wind_speed=2.0 + (i % 4),
                pm2_5=None,
                pm10=None,
                aqi=None,
                source_latency_ms=80.0,
                anomaly_score=0.0,
                is_anomaly=False,
            )
        )

        pm25 = 18.0 + (i % 8)
        pm10 = 32.0 + (i % 10)
        aqi = 55.0 + (i % 20)

        is_anomaly = (i % 11 == 0)
        if is_anomaly:
            pm25 = 95.0
            pm10 = 150.0
            aqi = 180.0

        rows.append(
            ObservationProcessResult(
                source="air_quality",
                location=location,
                observed_at=ts,
                latitude=25.03,
                longitude=121.56,
                temperature=None,
                humidity=None,
                wind_speed=None,
                pm2_5=pm25,
                pm10=pm10,
                aqi=aqi,
                source_latency_ms=95.0,
                anomaly_score=-0.8 if is_anomaly else 0.2,
                is_anomaly=is_anomaly,
            )
        )

    return rows
