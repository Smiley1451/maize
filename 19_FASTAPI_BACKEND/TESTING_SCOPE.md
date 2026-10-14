# Phase 19 — Automated API Testing Scope

## Coverage

The automated suite covers every route in the current OpenAPI contract: 30 HTTP endpoints, plus `/docs`, `/redoc`, and `/openapi.json` availability checks.

## Case classes

- Happy-path contract checks
- Missing required parameters
- Pydantic type and numeric-bound validation
- Empty and over-limit batches
- CSV and JSON upload success/failure paths
- Known and unknown model keys
- Dataset and artifact availability/not-found paths
- Pagination boundary checks
- Query/filter checks
- API-key protected endpoint: missing, wrong, and correct key
- Request-ID propagation
- Single prediction versus batch prediction result consistency
- OpenAPI route coverage regression guard

## Determinism

Endpoint tests use lightweight deterministic fakes for models, research datasets, and artifacts. This prevents test results from changing when the real model files change and keeps the API contract tests fast. The real model files are still validated by the existing Phase 19 verification/smoke tooling.

## Interpretation

A passing API suite means the HTTP layer, validation rules, routing, response contracts, authorization gate, file handling, and endpoint-to-service wiring satisfy the automated cases. It does not prove agronomic correctness of the underlying ML models; that remains the responsibility of the model validation phases.
