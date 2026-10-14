from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import APP_NAME, APP_VERSION, PROJECT_ROOT, BACKEND_ROOT, PORT
from app.services.data_service import DataService
from app.api.routes_models import service as model_service

router = APIRouter(tags=["System"])
_data = DataService()


@router.get("/info")
def info() -> dict:
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "backend_package_version": __version__,
        "project_root": str(PROJECT_ROOT),
        "backend_root": str(BACKEND_ROOT),
        "default_port": PORT,
        "models": model_service.info(),
        "datasets": _data.catalog(),
    }


@router.get("/features")
def features() -> dict:
    return {
        "base_features": [
            "days_to_50_percent_pollen_shedding",
            "days_to_50_percent_silking",
            "days_to_75_percent_dry_husk",
            "plant_height",
            "ear_height",
            "plant_stand",
            "shelling_percentage",
        ],
        "aliases_supported": {
            "plant_stand_000_per_ha": "plant_stand",
            "pollen_shedding_days": "days_to_50_percent_pollen_shedding",
            "silking_days": "days_to_50_percent_silking",
            "dry_husk_days": "days_to_75_percent_dry_husk",
            "plant_height_cm": "plant_height",
            "ear_height_cm": "ear_height",
            "shelling_pct": "shelling_percentage",
        },
        "engineered_features": ["silking_to_pollen_gap", "dry_husk_after_silking", "ear_height_ratio"],
    }


@router.get("/status")
def status() -> dict:
    available = sum(1 for x in model_service.info() if x["available"])
    return {"api": "UP", "project_root_exists": PROJECT_ROOT.exists(), "models_available": available, "models_total": len(model_service.info())}
