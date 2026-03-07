from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.metrics import metrics
from app.ml.anomaly import AnomalyService
from app.schemas.observation import ObservationIn, ObservationProcessResult
from app.services.repository import ObservationRepository

logger = logging.getLogger(__name__)


class ObservationProcessor:
    def __init__(self, anomaly_service: AnomalyService) -> None:
        self.anomaly_service = anomaly_service

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

    def process(self, payload: dict, db: Session):
        obs = ObservationIn.model_validate(payload)

        repo = ObservationRepository(db)
        self._fit_if_needed(repo, source=obs.source)
        anomaly = self.anomaly_service.score(obs)

        result = ObservationProcessResult(
            **obs.model_dump(),
            anomaly_score=anomaly.score,
            is_anomaly=anomaly.is_anomaly,
        )

        saved = repo.upsert(result)

        metrics.incr("worker_processed")
        if anomaly.is_anomaly:
            metrics.incr("anomaly_detected")
            logger.warning("anomaly detected source=%s location=%s at=%s", obs.source, obs.location, obs.observed_at)

        return saved
