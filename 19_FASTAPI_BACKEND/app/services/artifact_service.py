from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.core.config import PROJECT_ROOT
from app.services.path_registry import find_dataset


class ArtifactService:
    def _find_any(self, names: list[str]) -> Path | None:
        bases = [
            PROJECT_ROOT / "MAIZE_PHASES_16_18_DROP_IN" / "outputs",
            PROJECT_ROOT / "13_15_NEXT_PHASES" / "outputs",
            PROJECT_ROOT / "MAIZE_PHASES_13_15_DROP_IN" / "outputs",
            PROJECT_ROOT / "08_AUTOMATED_PIPELINE" / "outputs",
            PROJECT_ROOT / "10_12_NEXT_PHASES" / "outputs",
        ]
        for base in bases:
            if not base.exists():
                continue
            for name in names:
                try:
                    return next(base.rglob(name))
                except StopIteration:
                    continue
        return None

    def clustering(self) -> dict:
        p = self._find_any(["GENOTYPE_CLUSTERS.csv", "CLUSTER_PROFILES_MEDIAN.csv", "PCA_SCORES.csv"])
        if not p:
            return {"available": False, "files": {}}
        files = {}
        for n in ["GENOTYPE_CLUSTERS.csv", "CLUSTER_PROFILES_MEDIAN.csv", "KMEANS_SILHOUETTE.csv", "PCA_SCORES.csv", "PCA_VARIANCE.csv"]:
            q = self._find_any([n])
            if q:
                files[n] = str(q)
        return {"available": True, "files": files}

    def clustering_data(self, filename: str, limit: int, offset: int) -> dict:
        p = self._find_any([filename])
        if not p:
            return {"available": False, "filename": filename, "total": 0, "items": []}
        df = pd.read_csv(p, low_memory=False)
        part = df.iloc[offset : offset + limit]
        return {"available": True, "filename": filename, "path": str(p), "total": len(df), "limit": limit, "offset": offset, "items": part.where(pd.notna(part), None).to_dict(orient="records")}

    def weather_status(self) -> dict:
        status = self._find_any(["WEATHER_MODEL_STATUS.csv", "WEATHER_MODEL_BLOCKER.csv", "NEXT_DATA_NEEDED.txt", "WEATHER_INPUT_REQUIREMENTS.csv"])
        files = {}
        for n in ["WEATHER_MODEL_STATUS.csv", "WEATHER_MODEL_BLOCKER.csv", "NEXT_DATA_NEEDED.txt", "WEATHER_DERIVED_FEATURES.csv", "WEATHER_MONTHLY_2023_FEATURES.csv", "WEATHER_2023_SUMMARY_FEATURES.csv"]:
            q = self._find_any([n])
            if q:
                files[n] = str(q)
        return {"available": bool(status), "files": files}

    def explainability(self, model_key: str) -> dict:
        mapping = {
            "yield": ["YIELD_REGRESSION_PERMUTATION_IMPORTANCE.csv", "YIELD_PERMUTATION_IMPORTANCE.csv"],
            "tlb_regression": ["TLB_REGRESSION_PERMUTATION_IMPORTANCE.csv", "TLB_PERMUTATION_IMPORTANCE.csv"],
            "tlb_classifier": ["TLB_CLASSIFIER_PERMUTATION_IMPORTANCE.csv", "TLB_CLASSIFIER_PERMUTATION_IMPORTANCE.csv"],
            "sdm_regression": ["SDM_REGRESSION_PERMUTATION_IMPORTANCE.csv", "SDM_PERMUTATION_IMPORTANCE.csv"],
            "sdm_classifier": ["SDM_CLASSIFIER_PERMUTATION_IMPORTANCE.csv", "SDM_CLASSIFIER_PERMUTATION_IMPORTANCE.csv"],
        }
        names = mapping.get(model_key, [])
        p = self._find_any(names)
        if not p:
            return {"available": False, "model_key": model_key, "items": []}
        df = pd.read_csv(p)
        return {"available": True, "model_key": model_key, "path": str(p), "items": df.where(pd.notna(df), None).to_dict(orient="records")}
