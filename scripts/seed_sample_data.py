from __future__ import annotations

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.services.repository import ObservationRepository
from app.services.seed_data import build_seed_observations


def run_seed(location: str = "taipei", n: int = 24) -> int:
    init_db()
    rows = build_seed_observations(location=location, n=n)

    with SessionLocal() as db:
        repo = ObservationRepository(db)
        for row in rows:
            repo.upsert(row)

    return len(rows)


if __name__ == "__main__":
    inserted = run_seed()
    print(f"seed completed with {inserted} upserts")
