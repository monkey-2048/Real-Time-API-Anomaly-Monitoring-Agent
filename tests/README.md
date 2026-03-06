# Tests Layout

- `tests/phase1/unit/`: phase 1 unit tests
- `tests/phase1/integration/`: phase 1 integration-style tests
- `tests/phase2/`: phase 2 tests (new features)

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
