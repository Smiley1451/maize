# Phase 19 Contingency Plan

## Python not found
Run `python --version`. The backend expects Python 3.13.x or another supported Python 3.x.

## Dependencies fail
Run:
`powershell -ExecutionPolicy Bypass -File .\INSTALL_REQUIREMENTS.ps1 -UpgradePip`

## PowerShell NativeCommandError on Python warnings
The runner uses Python process exit codes for success/failure and does not use stderr presence as failure.

## Port 8000 already in use
Start on another port:
`.\RUN_PHASE19.ps1 -Action start -Port 8001`

## Models unavailable
The API remains healthy and exposes model availability through `/api/v1/models`. Prediction endpoints return model status `MODEL_UNAVAILABLE`; no fake prediction is generated.

## Dataset unavailable
Read-only data endpoints return an availability/status response or HTTP 404 for a requested unavailable domain. The application never invents records.

## Joblib/XGBoost load error
Install the same package family used when the model was trained. `xgboost` is included in this package because some model artifacts may require it for deserialization.

## API key
Set `MAIZE_API_KEY` in the environment to protect API routes. Health/docs remain accessible for operational checks.

## Future PostgreSQL migration
Phase 19 uses a repository/service layer around CSVs. Phase 22 can replace `DataService` with a PostgreSQL repository without changing the route contracts.
