# Phase 19 — FastAPI Backend Drop-In

This folder is a drop-in backend for the existing MAIZE AI/ML Digitalization Project. It exposes the trained models, prediction engine, research datasets, clustering results, weather-readiness artifacts, explainability outputs, and project verification artifacts through a versioned FastAPI interface.

## Windows start

Copy this folder into the existing project root. From the project root run only:

```powershell
.\19_FASTAPI_BACKEND\RUN_PHASE19.ps1
```

The menu provides:

```text
1 = Start API (foreground)
2 = Start API in background
3 = Run API smoke tests
4 = Verify Phase 19
5 = Install requirements
6 = API status
7 = Export OpenAPI schema
8 = Open Swagger docs
9 = Exit
```

A direct start is also available:

```powershell
.\19_FASTAPI_BACKEND\RUN_PHASE19.ps1 -Action start
```

Default URLs:

- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## API groups

### System
- `GET /health`
- `GET /ready`
- `GET /api/v1/status`
- `GET /api/v1/info`
- `GET /api/v1/features`

### Models
- `GET /api/v1/models`
- `GET /api/v1/models/{model_key}`
- `POST /api/v1/models/reload`

Model keys are:

```text
yield
tlb_regression
tlb_classifier
sdm_regression
sdm_classifier
```

### Prediction
- `POST /api/v1/predict/yield`
- `POST /api/v1/predict/tlb`
- `POST /api/v1/predict/sdm`
- `POST /api/v1/predict/all`
- `POST /api/v1/predict/batch`
- `POST /api/v1/predict/batch-csv`
- `POST /api/v1/predict/batch-json`

The prediction engine uses the packaged model feature schema when present, supports the existing column aliases, performs the same basic engineered-feature calculations as the Phase 18 runtime, and reports range flags without clipping predictions.

### Research data
- `GET /api/v1/catalog`
- `GET /api/v1/genotypes`
- `GET /api/v1/genotypes/{genotype}`
- `GET /api/v1/experiments`
- `GET /api/v1/observations`
- `GET /api/v1/disease/tlb`
- `GET /api/v1/disease/sdm`

The data layer prefers Phase 11 strict production datasets and falls back to compatible existing datasets if those are not present.

### Analytics/artifacts
- `GET /api/v1/clusters/status`
- `GET /api/v1/clusters/data`
- `GET /api/v1/weather/status`
- `GET /api/v1/explainability/{model_key}`
- `GET /api/v1/model-metrics`
- `GET /api/v1/dataset-summary/{domain}`

### Project artifacts
- `GET /api/v1/project/verification`
- `GET /api/v1/project/files`

## Prediction input

Example:

```json
{
  "genotype": "SAMPLE-GENOTYPE",
  "days_to_50_percent_pollen_shedding": 70,
  "days_to_50_percent_silking": 72,
  "days_to_75_percent_dry_husk": 112,
  "plant_height": 220,
  "ear_height": 115,
  "plant_stand": 70000,
  "shelling_percentage": 82
}
```

`plant_stand_000_per_ha` is also accepted and is converted to `plant_stand` internally.

## Security

For local development no key is required. To protect the API, set:

```powershell
$env:MAIZE_API_KEY="your-secret"
```

Clients then send `X-API-Key: your-secret`. Health and documentation endpoints remain available for operational checks.

## Architecture

```text
FastAPI routes
    ↓
Pydantic request schemas
    ↓
Services
    ├── ModelService
    ├── DataService
    ├── ArtifactService
    └── PathRegistry
    ↓
Existing project CSVs + packaged joblib models
```

The repository/service boundary is intentional: Phase 22 can replace CSV-backed reads with PostgreSQL without requiring route redesign.

## Important behavior

No endpoint fabricates a missing prediction, genotype, disease observation, or weather label. When a model or dataset is unavailable, the API exposes that status explicitly.

## Complete automated API testing

Run the complete API test suite without manually testing endpoints:

```powershell
.\RUN_PHASE19.ps1 -Action test
```

The suite currently runs 83 pytest cases covering all 30 OpenAPI HTTP endpoints, plus Swagger/ReDoc/OpenAPI availability. It checks happy paths, invalid inputs, numeric boundaries, pagination, file uploads, batch limits, authentication, request IDs, not-found behavior, and single-vs-batch prediction consistency.

The terminal prints each test case with `PASSED`/`FAILED` and then a final summary. Reports are written to `outputs/API_TEST_RESULTS.xml`, `outputs/API_TEST_CASES.csv`, and `outputs/API_TEST_REPORT.md`.
