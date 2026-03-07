from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.metrics import metrics
from app.ml.anomaly import AnomalyService
from app.schemas.observation import ObservationIn, ObservationProcessResult
from app.services.repository import ObservationRepository

logger = logging.getLogger(__name__)
settings = get_settings()


class ObservationProcessor:
    def __init__(self, anomaly_service: AnomalyService) -> None:
        self.anomaly_service = anomaly_service
        self._consecutive_anomaly_counter: dict[tuple[str, str], int] = {}

    def _fit_if_needed(self, repo: ObservationRepository, source: str) -> None:
        if self.anomaly_service.is_source_fitted(source):
            return

        rows = repo.recent_for_training_by_source(source=source, limit=300)
        samples = [
            ObservationIn(
                source=r.source,
                location=r.location,
                observed_at=r.observed_at,
                latitude=r.latitude,
                longitude=r.longitude,
                temperature=r.temperature,
                humidity=r.humidity,
                wind_speed=r.wind_speed,
                pm2_5=r.pm25,
                pm10=r.pm10,
                aqi=r.aqi,
                source_latency_ms=r.source_latency_ms,
            )
            for r in rows
        ]
        self.anomaly_service.fit(samples, source=source)

    def _apply_consecutive_gate(self, obs: ObservationIn, raw_is_anomaly: bool) -> bool:
        key = (obs.source, obs.location)
        if raw_is_anomaly:
            self._consecutive_anomaly_counter[key] = self._consecutive_anomaly_counter.get(key, 0) + 1
        else:
            self._consecutive_anomaly_counter[key] = 0

        return self._consecutive_anomaly_counter[key] >= settings.anomaly_consecutive_threshold

    def process(self, payload: dict, db: Session):
        obs = ObservationIn.model_validate(payload)

        repo = ObservationRepository(db)
        self._fit_if_needed(repo, source=obs.source)
        anomaly = self.anomaly_service.score(obs)
        final_is_anomaly = self._apply_consecutive_gate(obs, anomaly.is_anomaly)

        result = ObservationProcessResult(
            **obs.model_dump(),
            anomaly_score=anomaly.score,
            is_anomaly=final_is_anomaly,
        )

        saved = repo.upsert(result)

        metrics.incr("worker_processed")
        if final_is_anomaly:
            metrics.incr("anomaly_detected")
            logger.warning("anomaly detected source=%s location=%s at=%s", obs.source, obs.location, obs.observed_at)

        return saved
