from datetime import datetime, timedelta, timezone

from app.ml.anomaly import AnomalyService
from app.schemas.observation import ObservationIn


def make_obs(i: int, temp: float = 25.0, pm25: float = 20.0) -> ObservationIn:
    return ObservationIn(
        source="weather",
        location="taipei",
        observed_at=datetime(2026, 3, 6, tzinfo=timezone.utc) + timedelta(minutes=i),
        latitude=25.03,
        longitude=121.56,
        temperature=temp,
        humidity=60,
        wind_speed=4.0,
        pm2_5=pm25,
        pm10=35,
        aqi=55,
        source_latency_ms=50,
    )


def test_anomaly_service_cold_start_heuristic_flags_extreme():
    svc = AnomalyService()
    extreme = make_obs(1, temp=50.0, pm25=120.0)
    result = svc.score(extreme)

    assert result.is_anomaly is True


def test_anomaly_service_can_fit_and_score():
    svc = AnomalyService()
    baseline = [make_obs(i, temp=24.0 + (i % 3), pm25=18.0 + (i % 4)) for i in range(30)]
    svc.fit(baseline)

    normal = make_obs(999, temp=25.0, pm25=20.0)
    result = svc.score(normal)

    assert isinstance(result.score, float)
    assert isinstance(result.is_anomaly, bool)
