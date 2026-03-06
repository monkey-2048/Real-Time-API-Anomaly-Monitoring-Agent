from datetime import datetime, timezone

from app.services.normalizer import normalize_air_quality_payload, normalize_weather_payload


def test_normalize_weather_payload_maps_fields():
    raw = {
        "latitude": 25.03,
        "longitude": 121.56,
        "current": {
            "time": "2026-03-06T08:00:00Z",
            "temperature_2m": 26.4,
            "relative_humidity_2m": 70,
            "wind_speed_10m": 3.5,
        },
    }
    obs = normalize_weather_payload(raw, location="taipei", latency_ms=101.2)

    assert obs.source == "weather"
    assert obs.location == "taipei"
    assert obs.observed_at == datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc)
    assert obs.temperature == 26.4
    assert obs.humidity == 70
    assert obs.wind_speed == 3.5
    assert obs.source_latency_ms == 101.2


def test_normalize_air_quality_payload_maps_fields():
    raw = {
        "latitude": 25.03,
        "longitude": 121.56,
        "current": {
            "time": "2026-03-06T08:00:00Z",
            "pm2_5": 18.5,
            "pm10": 26.0,
            "us_aqi": 55,
        },
    }

    obs = normalize_air_quality_payload(raw, location="taipei", latency_ms=87.4)

    assert obs.source == "air_quality"
    assert obs.pm25 == 18.5
    assert obs.pm10 == 26.0
    assert obs.aqi == 55
    assert obs.source_latency_ms == 87.4
