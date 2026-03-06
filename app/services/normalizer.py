from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.observation import ObservationIn


def _safe_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_weather_payload(raw: dict, location: str, latency_ms: float | None = None) -> ObservationIn:
    current = raw.get("current", {})
    observed_at = current.get("time")
    dt = datetime.fromisoformat(observed_at.replace("Z", "+00:00")) if observed_at else datetime.now(timezone.utc)
    return ObservationIn(
        source="weather",
        location=location,
        observed_at=dt,
        latitude=float(raw.get("latitude")),
        longitude=float(raw.get("longitude")),
        temperature=_safe_float(current.get("temperature_2m")),
        humidity=_safe_float(current.get("relative_humidity_2m")),
        wind_speed=_safe_float(current.get("wind_speed_10m")),
        source_latency_ms=latency_ms,
    )


def normalize_air_quality_payload(raw: dict, location: str, latency_ms: float | None = None) -> ObservationIn:
    current = raw.get("current", {})
    observed_at = current.get("time")
    dt = datetime.fromisoformat(observed_at.replace("Z", "+00:00")) if observed_at else datetime.now(timezone.utc)
    return ObservationIn(
        source="air_quality",
        location=location,
        observed_at=dt,
        latitude=float(raw.get("latitude")),
        longitude=float(raw.get("longitude")),
        pm2_5=_safe_float(current.get("pm2_5")),
        pm10=_safe_float(current.get("pm10")),
        aqi=_safe_float(current.get("us_aqi")),
        source_latency_ms=latency_ms,
    )
