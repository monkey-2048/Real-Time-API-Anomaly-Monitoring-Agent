from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.metrics import metrics
from app.db.session import get_db_session
from app.schemas.observation import ObservationOut
from app.schemas.report import SummaryReport
from app.services.report_service import ReportService
from app.services.repository import ObservationRepository

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    queue = request.app.state.queue
    queue_length = await queue.length()
    return {
        "status": "ok",
        "service": "EnvPulse",
        "queue_length": queue_length,
        "metrics": metrics.snapshot(),
    }


@router.get("/observations", response_model=list[ObservationOut])
def observations(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
):
    repo = ObservationRepository(db)
    return repo.list_observations(limit=limit)


@router.get("/anomalies", response_model=list[ObservationOut])
def anomalies(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db_session),
):
    repo = ObservationRepository(db)
    return repo.list_anomalies(limit=limit)


@router.get("/report/summary", response_model=SummaryReport)
def report_summary(db: Session = Depends(get_db_session)):
    repo = ObservationRepository(db)
    return ReportService(repo).summary()
