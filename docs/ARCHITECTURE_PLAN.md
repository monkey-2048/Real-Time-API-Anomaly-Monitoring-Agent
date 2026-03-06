# EnvPulse Architecture Plan

## 1) Folder Structure

```text
envpulse/
  app/
    api/
      routes.py
    core/
      config.py
      logging.py
      metrics.py
    db/
      base.py
      session.py
      init_db.py
    models/
      observation.py
    schemas/
      observation.py
      report.py
    services/
      adapters.py
      normalizer.py
      queue.py
      repository.py
      processor.py
      report_service.py
    workers/
      worker.py
    scheduler/
      scheduler.py
    ml/
      anomaly.py
    utils/
      retries.py
    main.py
  tests/
    test_normalizer.py
    test_anomaly_service.py
    test_idempotent_write.py
  scripts/
    run_worker.py
    run_scheduler.py
  docker/
    Dockerfile.api
    Dockerfile.worker
    Dockerfile.scheduler
  docs/
    ARCHITECTURE_PLAN.md
  .env.example
  requirements.txt
  docker-compose.yml
  README.md
```

## 2) Architecture Flow

Scheduler/Producer -> External APIs -> Redis Queue -> Worker -> DB -> Report API

- Scheduler periodically triggers data collection.
- Source adapters fetch weather + air quality data.
- Normalizer maps raw payloads into one internal observation schema.
- Queue producer publishes normalized jobs to Redis list.
- Worker consumes jobs, applies feature extraction and anomaly detection.
- Repository writes to DB with idempotent upsert on `(source, location, observed_at)`.
- FastAPI exposes health, observation, anomaly, and summary report endpoints.

## 3) Key File Responsibilities

- `app/core/config.py`: Environment variable settings and app-wide config.
- `app/core/logging.py`: Structured logging setup.
- `app/core/metrics.py`: In-memory counters and latency tracking.
- `app/db/session.py`: SQLAlchemy engine/session factory.
- `app/models/observation.py`: Observation table with unique constraint for idempotency.
- `app/services/adapters.py`: External API adapters + fallback mock AQ source.
- `app/services/normalizer.py`: Converts raw source responses into unified schema.
- `app/services/queue.py`: Redis enqueue/dequeue wrapper with payload JSON serialization.
- `app/services/repository.py`: DB access and idempotent upsert/query methods.
- `app/ml/anomaly.py`: IsolationForest-based anomaly scoring service.
- `app/services/processor.py`: Worker business flow: validate -> detect anomaly -> persist.
- `app/workers/worker.py`: Queue consumer loop with retries and error handling.
- `app/scheduler/scheduler.py`: APScheduler job definitions and periodic producer logic.
- `app/api/routes.py`: API endpoints for health/observations/anomalies/summary.
- `app/main.py`: FastAPI app startup/shutdown lifecycle.
- `tests/*`: unit + integration-style tests for normalization, anomaly, idempotent writes.

## 4) Engineering Notes

- Idempotency is enforced by DB-level unique constraint + SQLAlchemy upsert.
- Graceful degradation: if one source fails, the other source still produces jobs.
- Retry/timeout policy is in adapter calls and worker processing.
- SQLite is default for local use; DB config is abstracted for PostgreSQL migration.
- Metrics are intentionally lightweight but expose production thinking.
