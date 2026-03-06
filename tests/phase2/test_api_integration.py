from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes import router
from app.db.base import Base
from app.db.session import get_db_session
from app.schemas.observation import ObservationProcessResult
from app.services.repository import ObservationRepository


class FakeQueue:
    async def length(self) -> int:
        return 3


def build_test_client(tmp_path):
    db_file = tmp_path / "api_integration.db"
    engine = create_engine(f"sqlite:///{db_file}", future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    app = FastAPI()
    app.include_router(router)
    app.state.queue = FakeQueue()

    def override_get_db_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    return TestClient(app), TestingSessionLocal


def seed_observations(TestingSessionLocal):
    with TestingSessionLocal() as db:
        repo = ObservationRepository(db)
        repo.upsert(
            ObservationProcessResult(
                source="weather",
                location="taipei",
                observed_at=datetime(2026, 3, 6, 8, 0, tzinfo=timezone.utc),
                latitude=25.03,
                longitude=121.56,
                temperature=24,
                humidity=65,
                wind_speed=4.1,
                pm2_5=None,
                pm10=None,
                aqi=None,
                source_latency_ms=90,
                anomaly_score=0.1,
                is_anomaly=False,
            )
        )
        repo.upsert(
            ObservationProcessResult(
                source="air_quality",
                location="taipei",
                observed_at=datetime(2026, 3, 6, 8, 5, tzinfo=timezone.utc),
                latitude=25.03,
                longitude=121.56,
                temperature=None,
                humidity=None,
                wind_speed=None,
                pm2_5=95,
                pm10=130,
                aqi=170,
                source_latency_ms=110,
                anomaly_score=-0.9,
                is_anomaly=True,
            )
        )


def test_health_endpoint_returns_queue_and_metrics(tmp_path):
    client, _ = build_test_client(tmp_path)

    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["queue_length"] == 3
    assert "metrics" in payload


def test_observations_and_anomalies_endpoints(tmp_path):
    client, TestingSessionLocal = build_test_client(tmp_path)
    seed_observations(TestingSessionLocal)

    observations = client.get("/observations?limit=10")
    assert observations.status_code == 200
    assert len(observations.json()) == 2

    anomalies = client.get("/anomalies?limit=10")
    assert anomalies.status_code == 200
    body = anomalies.json()
    assert len(body) == 1
    assert body[0]["source"] == "air_quality"


def test_report_summary_endpoint(tmp_path):
    client, TestingSessionLocal = build_test_client(tmp_path)
    seed_observations(TestingSessionLocal)

    response = client.get("/report/summary")
    assert response.status_code == 200
    summary = response.json()

    assert summary["total_observations"] == 2
    assert summary["anomalies"] == 1
    assert summary["anomaly_ratio"] == 0.5
