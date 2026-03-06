from __future__ import annotations

from app.schemas.report import SummaryReport
from app.services.repository import ObservationRepository


class ReportService:
    def __init__(self, repo: ObservationRepository) -> None:
        self.repo = repo

    def summary(self) -> SummaryReport:
        s = self.repo.summary()
        ratio = s["anomaly_ratio"]
        if ratio > 0.2:
            note = "Elevated anomaly rate observed. Investigate upstream conditions and sensor quality."
        elif ratio > 0.08:
            note = "Moderate anomaly activity. Keep monitoring trend changes."
        else:
            note = "Stable environmental profile based on current observation history."

        return SummaryReport(**s, note=note)
