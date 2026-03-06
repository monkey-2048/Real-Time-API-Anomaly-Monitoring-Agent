# EnvPulse Interview Demo (3-5 Minutes)

## 0) Opening (15s)

"This project is EnvPulse, an AI-assisted environmental monitoring system.
It shows production-style architecture: scheduled ingestion, queue decoupling,
worker processing, idempotent persistence, anomaly detection, and observability."

## 1) Architecture Walkthrough (45s)

Use this flow:
`Scheduler/Producer -> External APIs -> Redis Queue -> Worker -> DB -> Report API`

What to emphasize:
- Scheduler polls weather + air-quality APIs on interval.
- Redis queue decouples ingestion from processing.
- Worker validates payloads, runs anomaly detection, then writes with upsert.
- API layer is read/report focused and fast.

## 2) Reliability and Data Quality (50s)

Highlight:
- Idempotency: unique key `(source, location, observed_at)` + upsert.
- Retry and timeout on external requests.
- Source isolation: if air API fails, fallback mock adapter keeps pipeline alive.
- Graceful worker loop: errors are counted/logged, loop continues.

## 3) AI/ML Part (45s)

Highlight:
- Model is `IsolationForest` on normalized feature vector.
- Features: temperature, humidity, wind speed, PM2.5, PM10, AQI, latency.
- Cold start strategy: rule-based heuristic before enough baseline samples.
- This keeps system practical without expensive training pipeline.

## 4) Live Demo Script (60-90s)

Run:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/e2e_docker_check.ps1
```

What interviewer sees:
- stack bootstraps with Docker
- health/metrics/observations/anomalies/report checks pass
- optional teardown handled automatically

## 5) Engineering Signals (30s)

Mention:
- phase-based test structure (`tests/phase1`, `tests/phase2`, `tests/phase3`)
- API integration tests and idempotency test
- GitHub Actions CI runs pytest on push/PR

## 6) Production Next Steps (30s)

- PostgreSQL + Alembic migrations
- Prometheus metrics export + centralized logs
- dead-letter queue and richer retry policy
- model artifact/version tracking and periodic retraining
- auth and rate limiting for external-facing APIs
