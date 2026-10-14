# Phase 19 API Tests

The `tests/` directory is the automated safety net for the complete FastAPI surface.

It covers all 30 OpenAPI HTTP endpoints currently exposed by the application, plus boundary and error cases for validation, pagination, authentication, batch inputs, file uploads, and cross-checks between single-row and batch predictions.

Run everything from the Phase 19 folder:

```powershell
.\RUN_PHASE19.ps1 -Action test
```

Or:

```powershell
python .\scripts\run_full_tests.py
```

The runner prints every individual case as PASS/FAIL and writes:

- `outputs/API_TEST_RESULTS.xml`
- `outputs/API_TEST_CASES.csv`
- `outputs/API_TEST_REPORT.md`

The OpenAPI route coverage test intentionally fails if a future endpoint is added to the application without adding it to the expected route set in the tests.
