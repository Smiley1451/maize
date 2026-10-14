from fastapi import APIRouter
router = APIRouter(tags=["Meta"])
@router.get("/version")
def version() -> dict:
    from app import __version__
    return {"version": __version__}
