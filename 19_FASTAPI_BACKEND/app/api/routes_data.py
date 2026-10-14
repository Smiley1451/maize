from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.services.data_service import DataService

router = APIRouter(tags=["Research Data"])
service = DataService()


@router.get("/catalog")
def catalog() -> dict:
    return {"datasets": service.catalog()}


@router.get("/genotypes")
def genotypes(query: str | None = None, domain: str | None = Query(default=None), limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)) -> dict:
    return service.genotypes(query, domain, limit, offset)


@router.get("/genotypes/{genotype}")
def genotype_detail(genotype: str) -> dict:
    result = service.genotype_detail(genotype)
    if not result["domains"]:
        raise HTTPException(status_code=404, detail=f"Genotype not found: {genotype}")
    return result


@router.get("/experiments")
def experiments(domain: str | None = None, query: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> dict:
    selected = [domain] if domain in {"yield", "tlb", "sdm", "multi_trait"} else ["yield", "tlb", "sdm", "multi_trait"]
    rows = []
    for d in selected:
        df, path = service.load(d)
        if df is None:
            continue
        ecols = [c for c in ["experiment_id", "experiment_no", "trial_no", "source_section", "location", "season", "year"] if c in df.columns]
        if not ecols:
            continue
        sub = service.search(df, query, ecols)
        rows.extend(sub[ecols].drop_duplicates().assign(domain=d, dataset=str(path)).to_dict(orient="records"))
    result = pd.DataFrame(rows).drop_duplicates().to_dict(orient="records") if rows else []
    return {"total": len(result), "limit": limit, "offset": offset, "items": result[offset : offset + limit]}


@router.get("/observations")
def observations(domain: str = Query(..., pattern="^(yield|tlb|sdm|multi_trait)$"), genotype: str | None = None, variable: str | None = None, experiment: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> dict:
    df, path = service.load(domain)
    if df is None:
        raise HTTPException(status_code=404, detail=f"No dataset available for domain={domain}")
    for q, cols in [
        (genotype, ["canonical_genotype", "canonical_genotype_candidate", "genotype", "entity_name", "raw_genotype_names"]),
        (variable, ["variable", "canonical_trait", "trait"]),
        (experiment, ["experiment_id", "experiment_no", "trial_no"]),
    ]:
        if q:
            df = service.search(df, q, cols)
    result = service.page(df.reset_index(drop=True), limit, offset)
    result["dataset"] = str(path)
    return result


@router.get("/disease/tlb")
def tlb_data(genotype: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> dict:
    return observations("tlb", genotype=genotype, limit=limit, offset=offset)


@router.get("/disease/sdm")
def sdm_data(genotype: str | None = None, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)) -> dict:
    return observations("sdm", genotype=genotype, limit=limit, offset=offset)
