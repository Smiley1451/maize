from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import MAX_BATCH_ROWS
from app.schemas.prediction import BatchPredictionRequest, MaizeInput, PredictionResponse
from app.api.routes_models import service as model_service

router = APIRouter(prefix="/predict", tags=["Predictions"])


def _run(payloads: list[dict[str, Any]], requested: set[str] | None = None) -> dict:
    if not payloads:
        raise HTTPException(status_code=400, detail="No records supplied")
    if len(payloads) > MAX_BATCH_ROWS:
        raise HTTPException(status_code=413, detail=f"Maximum batch size is {MAX_BATCH_ROWS}")
    df = pd.DataFrame(payloads)
    out = model_service.predict(df, requested=requested)
    records = out.where(pd.notna(out), None).to_dict(orient="records")
    statuses = {c.removesuffix("_model_status"): str(out[c].iloc[0]) if len(out) else "NO_ROWS" for c in out.columns if c.endswith("_model_status")}
    return {"count": len(records), "results": records, "model_status": statuses}


@router.post("/yield", response_model=PredictionResponse)
def predict_yield(payload: MaizeInput) -> dict:
    result = _run([payload.model_dump()], {"yield"})
    item = result["results"][0]
    return {"genotype": item["genotype"], "results": item, "model_status": result["model_status"], "warnings": [v for k, v in item.items() if k.endswith("warning") and v]}


@router.post("/tlb", response_model=PredictionResponse)
def predict_tlb(payload: MaizeInput) -> dict:
    result = _run([payload.model_dump()], {"tlb_regression", "tlb_classifier"})
    item = result["results"][0]
    return {"genotype": item["genotype"], "results": item, "model_status": result["model_status"], "warnings": [v for k, v in item.items() if k.endswith("warning") and v]}


@router.post("/sdm", response_model=PredictionResponse)
def predict_sdm(payload: MaizeInput) -> dict:
    result = _run([payload.model_dump()], {"sdm_regression", "sdm_classifier"})
    item = result["results"][0]
    return {"genotype": item["genotype"], "results": item, "model_status": result["model_status"], "warnings": [v for k, v in item.items() if k.endswith("warning") and v]}


@router.post("/all", response_model=PredictionResponse)
def predict_all(payload: MaizeInput) -> dict:
    result = _run([payload.model_dump()])
    item = result["results"][0]
    return {"genotype": item["genotype"], "results": item, "model_status": result["model_status"], "warnings": [v for k, v in item.items() if k.endswith("warning") and v]}


@router.post("/batch")
def predict_batch(payload: BatchPredictionRequest) -> dict:
    return _run([x.model_dump() for x in payload.records])


@router.post("/batch-csv")
async def predict_batch_csv(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV: {exc}") from exc
    if len(df) > MAX_BATCH_ROWS:
        raise HTTPException(status_code=413, detail=f"Maximum batch size is {MAX_BATCH_ROWS}")
    out = model_service.predict(df)
    return {"filename": file.filename, "count": len(out), "results": out.where(pd.notna(out), None).to_dict(orient="records")}


@router.post("/batch-json")
async def predict_batch_json(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Upload a .json file")
    content = await file.read()
    try:
        obj = json.loads(content.decode("utf-8"))
        records = obj if isinstance(obj, list) else [obj]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc
    return _run(records)
