# EnvPulse

EnvPulse is an AI-assisted environmental monitoring prototype designed for interview demos. It periodically collects weather and air-quality signals from public APIs, normalizes and queues jobs, processes them asynchronously, writes observations idempotently, detects anomalies with IsolationForest, and exposes report endpoints via FastAPI.

## 1. Project Overview

Key capabilities:
- Multi-source API ingestion (Open-Meteo weather + Open-Meteo air quality with mock fallback)
- Producer/consumer architecture with Redis queue
- Idempotent DB writes through unique composite key + upsert
- Lightweight anomaly detection (`IsolationForest`) with cold-start heuristic fallback
- Gemini API integration for environment advice based on latest temperature, humidity, and air-quality signals
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

Main folders:
- `app/` API, scheduler, worker, services, ML
- `tests/` phase-based tests
- `scripts/` helper scripts
- `docker/` Dockerfiles

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
3. API will be available at `http://127.0.0.1:18080`.
4. Frontend dashboard will be available at `http://127.0.0.1:18080/frontend`.

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
- `GET /report/advice`
  - Gemini-based environment advice from latest temperature/humidity/PM2.5 snapshot

Gemini setup:
- put your key into `.env` as `GEMINI_API_KEY=your_key_here`
- endpoint: `GET /report/advice`
- frontend: click `Get AI Advice` to request Gemini suggestions on demand
- set `GEMINI_MODEL=gemini-2.5-flash` for current available model support

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

## 13. Core Requirement Verification

Use these steps to explicitly verify key engineering requirements:

1. Verify idempotency:
   - Start stack with `docker compose up --build`
   - Call `GET /report/summary` and note `total_observations`
   - Run `docker compose exec api python -m scripts.seed_sample_data` twice
   - Call `GET /report/summary` again and confirm rows are upserted (no duplicate growth from same composite key)

2. Verify scaling:
   - Start an extra worker: `docker compose up -d --scale worker=2`
   - Watch `docker compose logs --tail=100 worker`
   - Confirm queue drains normally and jobs are processed by multiple workers

3. Verify anomaly detection:
   - Call `GET /anomalies?limit=20`
   - Confirm anomaly records include `anomaly_score` and `is_anomaly=true`

4. Verify source failure handling:
   - Stop scheduler container and restart with invalid air-quality URL for test, or temporarily block network to AQ source
   - Observe logs and `GET /metrics`
   - Confirm fallback behavior is triggered and pipeline continues instead of full stop

## 14. Demo Flow (Video / Live)

Use this fixed order for a clean demo:

1. One-sentence project intro
2. Architecture flow (`Scheduler -> Queue -> Worker -> DB -> API`)
3. Start docker compose
4. Show `/health` and `/metrics`
5. Show `/observations` and `/anomalies`
6. Re-run seed/same data to show idempotency
7. Scale workers and explain horizontal processing
8. Show AI advice endpoint and frontend button flow

## 15. AI vs Manual Contribution

- Architecture, queue design, idempotency strategy, anomaly workflow, and system integration decisions were designed and implemented by me.
- AI assistance was used for wording refinement, boilerplate acceleration, and minor implementation speed-up.
- Core backend behavior, reliability design, and verification logic are my own engineering decisions.
