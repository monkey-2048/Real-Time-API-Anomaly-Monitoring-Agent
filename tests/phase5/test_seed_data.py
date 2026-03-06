from sqlalchemy import select

from app.models.observation import Observation
from app.services.repository import ObservationRepository
from app.services.seed_data import build_seed_observations


def test_build_seed_observations_count_and_content():
    rows = build_seed_observations(location="taipei", n=5)

    assert len(rows) == 10
    assert rows[0].source == "weather"
    assert rows[1].source == "air_quality"


def test_seed_upsert_idempotency_with_repository(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.base import Base

    db_file = tmp_path / "phase5_seed.db"
    engine = create_engine(f"sqlite:///{db_file}", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, future=True)

    rows = build_seed_observations(location="taipei", n=4)

    with SessionLocal() as db:
        repo = ObservationRepository(db)
        for row in rows:
            repo.upsert(row)
        for row in rows:
            repo.upsert(row)

        all_rows = db.execute(select(Observation)).scalars().all()
        assert len(all_rows) == 8
