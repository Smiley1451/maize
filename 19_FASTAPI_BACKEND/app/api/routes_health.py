from fastapi import APIRouter

from app.core.config import APP_VERSION, PROJECT_ROOT

router = APIRouter(tags=["System"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "project_root": str(PROJECT_ROOT), "api_version": APP_VERSION}


@router.get("/ready")
def ready() -> dict:
    return {"status": "ready", "project_root_exists": PROJECT_ROOT.exists()}
