# EnvPulse Final Interview One-Pager

## 1) 20-second intro

EnvPulse is a production-style environmental monitoring prototype.
It polls public weather and air-quality APIs, normalizes data, pushes jobs to Redis,
processes asynchronously with workers, stores idempotently, runs anomaly detection,
and serves report endpoints via FastAPI.

## 2) Architecture in one line

Scheduler/Producer -> External APIs -> Redis Queue -> Worker -> SQLite(DB) -> Report API

## 3) What to demo (live order)

1. Start stack
```powershell
docker compose up -d --build
```

2. Run quick API checks
```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

3. Run full e2e smoke check
```powershell
powershell -ExecutionPolicy Bypass -File scripts/e2e_docker_check.ps1
```

4. Show tests
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 4) Key engineering points to say

- Idempotency:
  unique key `(source, location, observed_at)` + upsert (`ON CONFLICT DO UPDATE`).

- Reliability:
  timeout + retry for API calls, source-level graceful degradation,
  mock AQ fallback when public AQ API fails.

- Scalability:
  producer and worker are decoupled by Redis queue,
  multiple workers can be added without API changes.

- AI integration:
  IsolationForest on normalized features,
  cold-start heuristic before enough baseline samples.

- Observability:
  `/health` and `/metrics` expose counters/latencies/gauges/events.

## 5) Endpoints to memorize

- `GET /health`
- `GET /metrics`
- `GET /observations`
- `GET /anomalies`
- `GET /report/summary`

## 6) If interviewer asks "what would you do next?"

- Move SQLite to PostgreSQL + Alembic migrations.
- Export metrics to Prometheus/Grafana.
- Add dead-letter queue and richer retry policies.
- Add model versioning and scheduled retraining.
- Add auth/rate-limit for external consumers.

## 7) Fast troubleshooting script

- If no observation data:
  check scheduler and worker logs, then `/metrics` counters (`jobs_enqueued`, `worker_processed`).

- If queue keeps growing:
  likely worker issue; verify worker container and `worker_failed` counter.

- If AQ source unstable:
  confirm fallback via `air_quality_mock_used` counter.
