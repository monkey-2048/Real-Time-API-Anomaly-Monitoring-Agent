# EnvPulse

EnvPulse is an AI-assisted environmental monitoring prototype designed for interview demos. It periodically collects weather and air-quality signals from public APIs, normalizes and queues jobs, processes them asynchronously, writes observations idempotently, detects anomalies with IsolationForest, and exposes report endpoints via FastAPI.

## 1. Project Overview

Key capabilities:
- Multi-source API ingestion (Open-Meteo weather + Open-Meteo air quality with mock fallback)
- Producer/consumer architecture with Redis queue
- Idempotent DB writes through unique composite key + upsert
- Lightweight anomaly detection (`IsolationForest`) with cold-start heuristic fallback
- Monitoring-minded logging and metrics counters
- Dockerized API / worker / scheduler services

## 2. Architecture

Pipeline:

`Scheduler/Producer -> External APIs -> Redis Queue -> Worker -> DB -> Report API`

- Scheduler/Producer: periodically polls external APIs and pushes normalized observation jobs.
- Redis Queue: decouples ingestion from processing so workers can scale horizontally.
- Worker: validates payloads, fits/scores anomaly model, and upserts observations.
- Database: SQLite by default (swap-friendly for PostgreSQL later).
- Report API: serves health, observations, anomalies, and summary endpoints.

## 3. Why This Demonstrates AI/Agent/Model/Network Engineering

- Network integration: real external API calls, timeout/retry, and source-level failure isolation.
- Async system design: scheduler and worker are decoupled through queue, enabling independent scaling.
- Model integration: IsolationForest scoring wired into production-like processing flow.
- Data engineering rigor: normalization contracts, idempotent persistence, and test coverage.
- Observability: latency and success/failure/anomaly counters exposed through health API.

## 4. Folder Structure

See [docs/ARCHITECTURE_PLAN.md](docs/ARCHITECTURE_PLAN.md) for detailed responsibilities.

## 5. Setup (Local)

1. Create and activate Python 3.11+ virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create env file:
   ```bash
   cp .env.example .env
   ```
4. Start Redis (locally or Docker).
5. Run services in separate terminals:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   python scripts/run_worker.py
   python scripts/run_scheduler.py
   ```

Seed demo data (optional, useful when external APIs are unstable):
```bash
python scripts/seed_sample_data.py
```

## 6. Run with Docker

1. Copy env template:
   ```bash
   cp .env.example .env
   ```
2. Start stack:
   ```bash
   docker compose up --build
   ```
3. API will be available at `http://localhost:8000`.

## 7. API Endpoints

- `GET /health`
  - queue length + in-memory metrics snapshot
- `GET /metrics`
  - runtime metrics snapshot (counters/latencies/gauges/events)
- `GET /observations?limit=100`
  - latest stored observations
- `GET /anomalies?limit=100`
  - stored anomalous observations
- `GET /report/summary`
  - aggregate metrics + short status note

## 8. Idempotency Design

Observation table has unique constraint:
- `(source, location, observed_at)`

Worker uses SQLite upsert (`ON CONFLICT DO UPDATE`) so re-running the same scheduled fetch updates the same row instead of creating duplicates.

## 9. Scaling Design

- Scheduler scales independently from workers.
- Multiple worker instances can consume from the same Redis queue.
- API service stays responsive because heavy processing is offloaded to worker.
- DB layer is repository-based, so backend migration from SQLite to PostgreSQL is straightforward.

## 10. Error Handling and Degradation

- HTTP timeout + retry for external APIs.
- Per-source failure handling in producer (`gather(..., return_exceptions=True)`).
- Air-quality adapter falls back to mock source when public API fails.
- Worker catches payload/process failures and continues loop.

## 11. Monitoring and Observability

Tracked examples:
- API latency (weather/air-quality)
- API success/failure counters
- jobs enqueued
- worker processed/failed
- anomaly detected count

`GET /health` and `GET /metrics` expose runtime diagnosis snapshots.

## 12. Anomaly Detection Approach

- Model: `IsolationForest` (good for unsupervised anomaly detection on tabular numeric features)
- Feature set:
  - temperature, humidity, wind speed
  - PM2.5, PM10, AQI
  - source latency (optional signal)
- Cold start:
  - before minimum training samples are reached, system uses transparent heuristic thresholds

### Why IsolationForest
- lightweight and fast
- no labels required
- robust enough for interview-scale anomaly demo

## 13. Trade-offs

- In-memory metrics reset on process restart (simple, demo-friendly).
- No distributed tracing stack (OpenTelemetry/Prometheus left for future).
- No migration tool (Alembic) to keep prototype setup minimal.

## 14. Production Upgrades (Next)

1. Replace SQLite with PostgreSQL + Alembic migrations.
2. Add dead-letter queue and structured retry policies per failure category.
3. Persist model artifacts/versioning and add periodic retraining job.
4. Export metrics to Prometheus and logs to centralized collector.
5. Add auth/rate-limit for report endpoints.

## 15. Demo Script

After services are running, quick-check endpoints:
```bash
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

Full Docker end-to-end smoke check:
```bash
powershell -ExecutionPolicy Bypass -File scripts/e2e_docker_check.ps1
```

## 16. Tests

Run:
```bash
pytest -q
```

Included tests:
- normalization mapping tests
- anomaly service tests (cold-start + fit/score)
- idempotent DB upsert integration-style test
- API integration tests for report/health endpoints

Interview script:
- `docs/INTERVIEW_DEMO_3_5_MIN.md`
- `docs/FINAL_INTERVIEW_ONE_PAGER.md`
