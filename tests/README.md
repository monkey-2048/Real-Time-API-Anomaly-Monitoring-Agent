# Tests Layout

- `tests/phase1/unit/`: phase 1 unit tests
- `tests/phase1/integration/`: phase 1 integration-style tests
- `tests/phase2/`: phase 2 tests (new features)
- `tests/phase3/`: phase 3 tests and e2e checklist
- `tests/phase5/`: phase 5 tests for seed/demo data

Run all tests:
```bash
pytest -q
```

Run phase 1 only:
```bash
pytest -q tests/phase1
```

Run phase 1 unit only:
```bash
pytest -q tests/phase1/unit
```

Run phase 1 integration only:
```bash
pytest -q tests/phase1/integration
```

Run phase 2 only:
```bash
pytest -q tests/phase2
```

Run phase 3 only:
```bash
pytest -q tests/phase3
```

Run phase 5 only:
```bash
pytest -q tests/phase5
```
