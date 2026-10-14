from __future__ import annotations

from pathlib import Path
import pandas as pd
from fastapi import APIRouter, Query

from app.core.config import PROJECT_ROOT
from app.services.artifact_service import ArtifactService

router = APIRouter(tags=["Analytics & Artifacts"])
service = ArtifactService()


@router.get("/clusters/status")
def clusters_status() -> dict:
    return service.clustering()


@router.get("/clusters/data")
def clusters_data(filename: str = Query("GENOTYPE_CLUSTERS.csv"), limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> dict:
    return service.clustering_data(filename, limit, offset)


@router.get("/weather/status")
def weather_status() -> dict:
    return service.weather_status()


@router.get("/explainability/{model_key}")
def explainability(model_key: str) -> dict:
    return service.explainability(model_key)


@router.get("/model-metrics")
def model_metrics(domain: str = Query(..., pattern="^(yield|tlb|sdm)$"), kind: str = Query("regression", pattern="^(regression|classification)$")) -> dict:
    candidates = {
        ("yield", "regression"): ["YIELD_MODEL_COMPARISON.csv", "TUNING_RESULTS.csv"],
        ("tlb", "regression"): ["TLB_REGRESSION_MODEL_COMPARISON.csv", "DISEASE_TUNING_RESULTS.csv"],
        ("tlb", "classification"): ["TLB_CLASSIFICATION_MODEL_COMPARISON.csv", "DISEASE_CLASSIFICATION_TUNING_RESULTS.csv"],
        ("sdm", "regression"): ["SDM_REGRESSION_MODEL_COMPARISON.csv", "DISEASE_TUNING_RESULTS.csv"],
        ("sdm", "classification"): ["SDM_CLASSIFICATION_MODEL_COMPARISON.csv", "DISEASE_CLASSIFICATION_TUNING_RESULTS.csv"],
    }[(domain, kind)]
    p = service._find_any(candidates)
    if not p:
        return {"available": False, "domain": domain, "kind": kind, "items": []}
    df = pd.read_csv(p)
    return {"available": True, "domain": domain, "kind": kind, "path": str(p), "items": df.where(pd.notna(df), None).to_dict(orient="records")}


@router.get("/dataset-summary/{domain}")
def dataset_summary(domain: str) -> dict:
    if domain not in {"yield", "tlb", "sdm", "multi_trait"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="domain must be yield, tlb, sdm, or multi_trait")
    from app.services.data_service import DataService
    ds = DataService()
    df, path = ds.load(domain)
    if df is None:
        return {"available": False, "domain": domain}
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        summary = []
    else:
        desc = numeric.describe().transpose().reset_index(names="feature")
        desc = desc.where(pd.notna(desc), None)
        summary = desc.to_dict(orient="records")
    return {"available": True, "domain": domain, "path": str(path), "rows": len(df), "columns": list(df.columns), "numeric_summary": summary}
