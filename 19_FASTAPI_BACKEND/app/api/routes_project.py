from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.core.config import PROJECT_ROOT

router = APIRouter(prefix="/project", tags=["Project"])


def first_existing(*paths: Path) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


@router.get("/verification")
def project_verification() -> dict:
    candidates = [
        PROJECT_ROOT / "08_AUTOMATED_PIPELINE" / "outputs" / "09_FINAL_VERIFICATION" / "FINAL_STATUS.json",
        PROJECT_ROOT / "MAIZE_PHASES_16_18_DROP_IN" / "outputs" / "18_PREDICTION_ENGINE" / "MODEL_AVAILABILITY.csv",
        PROJECT_ROOT / "09_FINAL_PROJECT_STATUS.md",
    ]
    found = [str(p) for p in candidates if p.exists()]
    final_json = candidates[0]
    payload = None
    if final_json.exists():
        try:
            payload = json.loads(final_json.read_text(encoding="utf-8"))
        except Exception:
            payload = None
    return {"project_root": str(PROJECT_ROOT), "available_artifacts": found, "final_status": payload}


@router.get("/files")
def project_files(prefix: str | None = None, limit: int = 200) -> dict:
    base = PROJECT_ROOT / prefix if prefix else PROJECT_ROOT
    if not base.exists() or not base.is_dir():
        return {"base": str(base), "total": 0, "items": []}
    items = []
    for p in base.rglob("*"):
        if p.is_file():
            try:
                rel = p.relative_to(PROJECT_ROOT)
            except ValueError:
                rel = p
            items.append({"path": str(rel), "size_bytes": p.stat().st_size})
            if len(items) >= max(1, min(limit, 1000)):
                break
    return {"base": str(base), "total_returned": len(items), "items": items}
