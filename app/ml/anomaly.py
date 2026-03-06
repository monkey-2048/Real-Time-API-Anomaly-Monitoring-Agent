from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.config import get_settings
from app.schemas.observation import ObservationIn

settings = get_settings()


@dataclass
class AnomalyResult:
    score: float
    is_anomaly: bool


class AnomalyService:
    def __init__(self) -> None:
        self._model = IsolationForest(
            contamination=settings.anomaly_contamination,
            random_state=42,
            n_estimators=100,
        )
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    @staticmethod
    def _to_vector(obs: ObservationIn) -> list[float]:
        return [
            float(obs.temperature or 0.0),
            float(obs.humidity or 0.0),
            float(obs.wind_speed or 0.0),
            float(obs.pm25 or 0.0),
            float(obs.pm10 or 0.0),
            float(obs.aqi or 0.0),
            float(obs.source_latency_ms or 0.0),
        ]

    def fit(self, samples: list[ObservationIn]) -> None:
        if len(samples) < settings.anomaly_min_samples:
            return
        x = np.array([self._to_vector(s) for s in samples])
        self._model.fit(x)
        self._is_fitted = True

    def score(self, observation: ObservationIn) -> AnomalyResult:
        vector = np.array([self._to_vector(observation)])
        if not self._is_fitted:
            # cold start fallback; keeps system usable before enough training data
            simple_score = float(np.mean(vector))
            heuristic_anomaly = (
                (observation.pm25 or 0) > 80
                or (observation.pm10 or 0) > 120
                or (observation.aqi or 0) > 150
                or (observation.temperature or 0) < -15
                or (observation.temperature or 0) > 45
            )
            return AnomalyResult(score=simple_score, is_anomaly=bool(heuristic_anomaly))

        raw_score = float(self._model.score_samples(vector)[0])
        pred = int(self._model.predict(vector)[0])
        return AnomalyResult(score=raw_score, is_anomaly=(pred == -1))
