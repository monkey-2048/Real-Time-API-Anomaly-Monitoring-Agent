from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ObservationIn(BaseModel):
    source: str
    location: str
    observed_at: datetime
    latitude: float
    longitude: float

    temperature: float | None = None
    humidity: float | None = None
    wind_speed: float | None = None

    pm25: float | None = Field(default=None, alias="pm2_5")
    pm10: float | None = None
    aqi: float | None = None

    source_latency_ms: float | None = None


class ObservationProcessResult(ObservationIn):
    anomaly_score: float | None = None
    is_anomaly: bool = False


class ObservationOut(BaseModel):
    id: int
    source: str
    location: str
    observed_at: datetime
    latitude: float
    longitude: float
    temperature: float | None
    humidity: float | None
    wind_speed: float | None
    pm25: float | None
    pm10: float | None
    aqi: float | None
    source_latency_ms: float | None
    anomaly_score: float | None
    is_anomaly: bool

    model_config = ConfigDict(from_attributes=True)
