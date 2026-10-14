from __future__ import annotations

from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import APP_NAME, APP_VERSION, API_PREFIX, API_KEY, CORS_ORIGINS, MAX_BATCH_ROWS, PROJECT_ROOT
from app.core.logging_setup import logger
from app.api import routes_health, routes_models, routes_predict, routes_data, routes_analytics, routes_info, routes_project


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("==============================================================")
    logger.info("PHASE 19: FASTAPI BACKEND STARTING")
    logger.info("PROJECT ROOT: %s", PROJECT_ROOT)
    logger.info("MAX BATCH ROWS: %s", MAX_BATCH_ROWS)
    logger.info("FASTAPI BACKEND STARTED")
    yield
    logger.info("FASTAPI BACKEND STOPPED")


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="API layer for the maize digitization, research-data, ML prediction, clustering, weather-readiness and explainability pipeline.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(routes_health.router)
app.include_router(routes_info.router, prefix=API_PREFIX)
app.include_router(routes_models.router, prefix=API_PREFIX)
app.include_router(routes_predict.router, prefix=API_PREFIX)
app.include_router(routes_data.router, prefix=API_PREFIX)
app.include_router(routes_analytics.router, prefix=API_PREFIX)
app.include_router(routes_project.router, prefix=API_PREFIX)


@app.middleware("http")
async def request_and_optional_api_key(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    if API_KEY and request.url.path not in {"/health", "/ready", "/docs", "/redoc", "/openapi.json"}:
        if request.headers.get("X-API-Key") != API_KEY:
            from fastapi.responses import JSONResponse
            response = JSONResponse(status_code=401, content={"detail": "Invalid or missing X-API-Key", "request_id": request_id})
            response.headers["X-Request-ID"] = request_id
            return response
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
