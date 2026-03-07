from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.schemas.observation import ObservationProcessResult


class ObservationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, data: ObservationProcessResult) -> Observation:
        values = {
            "source": data.source,
            "location": data.location,
            "observed_at": data.observed_at,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "temperature": data.temperature,
            "humidity": data.humidity,
            "wind_speed": data.wind_speed,
            "pm25": data.pm25,
            "pm10": data.pm10,
            "aqi": data.aqi,
            "source_latency_ms": data.source_latency_ms,
            "anomaly_score": data.anomaly_score,
            "is_anomaly": 1.0 if data.is_anomaly else 0.0,
        }

        stmt = sqlite_insert(Observation).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "location", "observed_at"],
            set_={
                "temperature": stmt.excluded.temperature,
                "humidity": stmt.excluded.humidity,
                "wind_speed": stmt.excluded.wind_speed,
                "pm25": stmt.excluded.pm25,
                "pm10": stmt.excluded.pm10,
                "aqi": stmt.excluded.aqi,
                "source_latency_ms": stmt.excluded.source_latency_ms,
                "anomaly_score": stmt.excluded.anomaly_score,
                "is_anomaly": stmt.excluded.is_anomaly,
            },
        )
        self.db.execute(stmt)
        self.db.commit()

        result = self.db.execute(
            select(Observation).where(
                Observation.source == data.source,
                Observation.location == data.location,
                Observation.observed_at == data.observed_at,
            )
        ).scalar_one()
        return result

    def list_observations(self, limit: int = 100) -> Sequence[Observation]:
        stmt: Select[tuple[Observation]] = select(Observation).order_by(Observation.observed_at.desc()).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def list_anomalies(self, limit: int = 100) -> Sequence[Observation]:
        stmt = (
            select(Observation)
            .where(Observation.is_anomaly == 1.0)
            .order_by(Observation.observed_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def recent_for_training(self, limit: int = 200) -> Sequence[Observation]:
        stmt = select(Observation).order_by(Observation.observed_at.desc()).limit(limit)
        return self.db.execute(stmt).scalars().all()

    def recent_for_training_by_source(self, source: str, limit: int = 200) -> Sequence[Observation]:
        stmt = (
            select(Observation)
            .where(Observation.source == source)
            .order_by(Observation.observed_at.desc())
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def latest_by_source(self, source: str) -> Observation | None:
        stmt = (
            select(Observation)
            .where(Observation.source == source)
            .order_by(Observation.observed_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def latest_signal_snapshot(self) -> dict | None:
        weather = self.latest_by_source("weather")
        air = self.latest_by_source("air_quality")
        if weather is None and air is None:
            return None

        ref = weather or air
        return {
            "location": ref.location,
            "observed_at": ref.observed_at.isoformat(),
            "temperature": weather.temperature if weather else None,
            "humidity": weather.humidity if weather else None,
            "wind_speed": weather.wind_speed if weather else None,
            "pm25": air.pm25 if air else None,
            "pm10": air.pm10 if air else None,
            "aqi": air.aqi if air else None,
        }

    def summary(self) -> dict:
        total = self.db.execute(select(func.count(Observation.id))).scalar_one()
        anomalies = self.db.execute(select(func.count(Observation.id)).where(Observation.is_anomaly == 1.0)).scalar_one()

        avg_temperature = self.db.execute(select(func.avg(Observation.temperature))).scalar_one()
        avg_humidity = self.db.execute(select(func.avg(Observation.humidity))).scalar_one()
        avg_pm25 = self.db.execute(select(func.avg(Observation.pm25))).scalar_one()
        avg_pm10 = self.db.execute(select(func.avg(Observation.pm10))).scalar_one()
        avg_aqi = self.db.execute(select(func.avg(Observation.aqi))).scalar_one()

        return {
            "total_observations": int(total or 0),
            "anomalies": int(anomalies or 0),
            "anomaly_ratio": float((anomalies / total) if total else 0.0),
            "avg_temperature": float(avg_temperature) if avg_temperature is not None else None,
            "avg_humidity": float(avg_humidity) if avg_humidity is not None else None,
            "avg_pm25": float(avg_pm25) if avg_pm25 is not None else None,
            "avg_pm10": float(avg_pm10) if avg_pm10 is not None else None,
            "avg_aqi": float(avg_aqi) if avg_aqi is not None else None,
        }
