from __future__ import annotations

from dataclasses import dataclass
import math

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
        self._models: dict[str, IsolationForest] = {}
        self._fitted_sources: set[str] = set()

    def is_source_fitted(self, source: str) -> bool:
        return source in self._fitted_sources

    @staticmethod
    def _vector_for_source(obs: ObservationIn) -> list[float]:
        # Source-specific vectors avoid mixing weather-null and AQ-null features.
        if obs.source == "weather":
            hour = float(obs.observed_at.hour)
            hour_angle = 2 * math.pi * (hour / 24.0)
            return [
                float(obs.temperature or 0.0),
                float(obs.humidity or 0.0),
                float(obs.wind_speed or 0.0),
                math.sin(hour_angle),
                math.cos(hour_angle),
            ]
        if obs.source == "air_quality":
            return [
                float(obs.pm25 or 0.0),
                float(obs.pm10 or 0.0),
                float(obs.aqi or 0.0),
            ]
        return [
            float(obs.temperature or 0.0),
            float(obs.humidity or 0.0),
            float(obs.wind_speed or 0.0),
            float(obs.pm25 or 0.0),
            float(obs.pm10 or 0.0),
            float(obs.aqi or 0.0),
        ]

    def fit(self, samples: list[ObservationIn], source: str) -> None:
        source_samples = [s for s in samples if s.source == source]
        if len(source_samples) < settings.anomaly_min_samples:
            return

        x = np.array([self._vector_for_source(s) for s in source_samples])
        model = IsolationForest(
            contamination=settings.anomaly_contamination,
            random_state=42,
            n_estimators=100,
        )
        model.fit(x)
        self._models[source] = model
        self._fitted_sources.add(source)

    def score(self, observation: ObservationIn) -> AnomalyResult:
        vector = np.array([self._vector_for_source(observation)])
        model = self._models.get(observation.source)

        if model is None:
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

        raw_score = float(model.score_samples(vector)[0])
        pred = int(model.predict(vector)[0])
        return AnomalyResult(score=raw_score, is_anomaly=(pred == -1))
