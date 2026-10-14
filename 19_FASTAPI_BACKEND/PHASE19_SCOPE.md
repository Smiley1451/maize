# Phase 19 Scope

This phase adds an HTTP API around the existing maize ML project without changing the source-preserved data.

### Included
- FastAPI application
- Pydantic request validation
- Yield/TLB/SDM prediction endpoints
- Batch JSON/CSV endpoints
- Model registry and reload
- Genotype and experiment search
- Observation APIs
- Disease observation APIs
- PCA/cluster artifact APIs
- Weather readiness API
- Explainability API
- Model metric API
- Project verification and file inventory APIs
- Optional API-key middleware
- CORS configuration
- Swagger/ReDoc/OpenAPI
- PowerShell launcher/install/test/verify scripts
- Dockerfile for later deployment

### Explicit non-goals
- PostgreSQL writes/CRUD (Phase 22)
- User authentication/identity management
- LLM assistant (Phase 21)
- Dashboard UI (Phase 20)
- Artificial filling of missing model predictions or weather labels
