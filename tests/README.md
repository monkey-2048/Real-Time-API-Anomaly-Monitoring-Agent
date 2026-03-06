# Tests Layout

- `tests/unit/`: pure unit tests (normalization, anomaly service)
- `tests/integration/`: DB/integration-style tests (idempotent upsert)

Run all tests:
```bash
pytest -q
```

Run only unit:
```bash
pytest -q tests/unit
```

Run only integration:
```bash
pytest -q tests/integration
```
