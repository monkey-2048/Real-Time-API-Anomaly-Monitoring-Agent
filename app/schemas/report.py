from pydantic import BaseModel


class SummaryReport(BaseModel):
    total_observations: int
    anomalies: int
    anomaly_ratio: float
    avg_temperature: float | None
    avg_humidity: float | None
    avg_pm25: float | None
    avg_pm10: float | None
    avg_aqi: float | None
    note: str
