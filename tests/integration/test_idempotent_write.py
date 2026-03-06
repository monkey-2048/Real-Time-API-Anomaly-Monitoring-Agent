from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.observation import Observation
from app.schemas.observation import ObservationProcessResult
from app.services.repository import ObservationRepository


def test_idempotent_upsert_no_duplicates(tmp_path):
    db_file = tmp_path / "test_envpulse.db"
    engine = create_engine(f"sqlite:///{db_file}", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    payload = ObservationProcessResult(
        source="weather",
        location="taipei",
        observed_at=datetime(2026, 3, 6, 12, 0, tzinfo=timezone.utc),
        latitude=25.03,
        longitude=121.56,
        temperature=26,
        humidity=70,
        wind_speed=3.2,
        pm2_5=None,
        pm10=None,
        aqi=None,
        source_latency_ms=100,
        anomaly_score=0.1,
        is_anomaly=False,
    )

    with SessionLocal() as db:
        repo = ObservationRepository(db)
        repo.upsert(payload)

        payload.temperature = 27
        repo.upsert(payload)

        count = db.execute(select(Observation)).scalars().all()
        assert len(count) == 1
        assert count[0].temperature == 27
