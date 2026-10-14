Configuration is environment-first. Copy `.env.example` to `.env` only if you want custom values.
For Phase 19, the API reads the existing project's CSV outputs and packaged joblib models. PostgreSQL is intentionally deferred to Phase 22; the repository service is isolated so a database repository can replace it later.
