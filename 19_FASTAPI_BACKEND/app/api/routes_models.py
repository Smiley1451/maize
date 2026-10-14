from fastapi import APIRouter, Depends

from app.core.security import require_api_key
from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["Models"])
service = ModelService()


@router.get("")
def models() -> dict:
    return {"models": service.info()}


@router.get("/{model_key}")
def model_detail(model_key: str) -> dict:
    for x in service.info():
        if x["model_key"] == model_key:
            return x
    return {"model_key": model_key, "available": False, "error": "Unknown model key"}


@router.post("/reload", dependencies=[Depends(require_api_key)])
def reload_models() -> dict:
    service.reload()
    return {"message": "Model reload complete", "models": service.info()}
