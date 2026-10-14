from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.core.logging_setup import logger
from app.services.path_registry import find_dataset


DATASET_MAP = {
    "yield": [
        "YIELD_PRODUCTION_STRICT.csv",
        "YIELD_EXPLORATORY_ALL_IDENTITIES.csv",
        "ML_YIELD_PIPELINE_READY.csv",
        "ML_YIELD_READY.csv",
    ],
    "tlb": [
        "TLB_PRODUCTION_STRICT.csv",
        "TLB_EXPLORATORY_ALL_IDENTITIES.csv",
        "TLB_REGRESSION_READY.csv",
    ],
    "sdm": [
        "SDM_PRODUCTION_STRICT.csv",
        "SDM_EXPLORATORY_ALL_IDENTITIES.csv",
        "SDM_REGRESSION_READY.csv",
    ],
    "multi_trait": [
        "MULTI_TRAIT_PRODUCTION_SUMMARY.csv",
        "ML_MULTI_TRAIT_EXPLORATORY.csv",
    ],
}


class DataService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[Path, float, pd.DataFrame]] = {}

    def locate(self, domain: str) -> Path | None:
        for name in DATASET_MAP.get(domain, []):
            p = find_dataset(name)
            if p:
                return p
        return None

    def load(self, domain: str) -> tuple[pd.DataFrame | None, Path | None]:
        p = self.locate(domain)
        if not p:
            return None, None
        mtime = p.stat().st_mtime
        cached = self._cache.get(domain)
        if cached and cached[0] == p and cached[1] == mtime:
            return cached[2], p
        try:
            df = pd.read_csv(p, low_memory=False)
            self._cache[domain] = (p, mtime, df)
            logger.info("DATASET LOADED: %s rows=%s domain=%s", p, len(df), domain)
            return df, p
        except Exception:
            logger.exception("DATASET LOAD FAILED: %s", p)
            raise

    def catalog(self) -> list[dict[str, Any]]:
        rows = []
        for domain in DATASET_MAP:
            p = self.locate(domain)
            df = None
            if p:
                try:
                    df, _ = self.load(domain)
                except Exception:
                    pass
            rows.append({"domain": domain, "available": bool(p), "path": str(p) if p else None, "rows": int(len(df)) if df is not None else 0, "columns": list(df.columns) if df is not None else []})
        return rows

    @staticmethod
    def page(df: pd.DataFrame, limit: int, offset: int) -> dict[str, Any]:
        part = df.iloc[offset : offset + limit]
        return {"total": int(len(df)), "limit": limit, "offset": offset, "items": part.where(pd.notna(part), None).to_dict(orient="records")}

    @staticmethod
    def search(df: pd.DataFrame, query: str | None, columns: list[str]) -> pd.DataFrame:
        if not query:
            return df
        q = query.lower().strip()
        mask = pd.Series(False, index=df.index)
        for c in columns:
            if c in df.columns:
                mask = mask | df[c].astype(str).str.lower().str.contains(q, regex=False, na=False)
        return df.loc[mask]

    def genotypes(self, query: str | None, domain: str | None, limit: int, offset: int) -> dict[str, Any]:
        domains = [domain] if domain in DATASET_MAP else list(DATASET_MAP.keys())
        names: dict[str, dict[str, Any]] = {}
        for d in domains:
            df, _ = self.load(d)
            if df is None or df.empty:
                continue
            gcol = next((c for c in ["canonical_genotype", "canonical_genotype_candidate", "genotype", "entity_name", "raw_genotype_names"] if c in df.columns), None)
            if not gcol:
                continue
            sub = self.search(df, query, [gcol])
            for g in sub[gcol].dropna().astype(str):
                names.setdefault(g, {"genotype": g, "domains": []})
                if d not in names[g]["domains"]:
                    names[g]["domains"].append(d)
        arr = sorted(names.values(), key=lambda x: x["genotype"].lower())
        return {"total": len(arr), "limit": limit, "offset": offset, "items": arr[offset : offset + limit]}

    def genotype_detail(self, genotype: str) -> dict[str, Any]:
        result: dict[str, Any] = {"genotype": genotype, "domains": {}}
        for domain in DATASET_MAP:
            df, path = self.load(domain)
            if df is None:
                continue
            gcol = next((c for c in ["canonical_genotype", "canonical_genotype_candidate", "genotype", "entity_name", "raw_genotype_names"] if c in df.columns), None)
            if not gcol:
                continue
            sub = df[df[gcol].astype(str).str.casefold() == genotype.casefold()]
            if not sub.empty:
                result["domains"][domain] = {
                    "dataset": str(path),
                    "rows": self.page(sub.reset_index(drop=True), 1000, 0)["items"],
                }
        return result
