from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Keep tests deterministic and independent of whatever trained models happen to be
# present on the caller's machine. The real model loader is still tested separately.
os.environ.setdefault("MAIZE_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("MAIZE_API_KEY", "")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.api import routes_analytics, routes_data, routes_info, routes_models, routes_predict  # noqa: E402
from app.core import security  # noqa: E402
from app.core import config  # noqa: E402
import app.services.data_service as data_service_module  # noqa: E402


class FakeModelService:
    """Small deterministic service used by endpoint tests.

    The fake exposes the same public interface as ModelService so the endpoint
    tests can compare single-row and batch results without loading large .joblib
    artifacts during every test.
    """

    KEYS = ["yield", "tlb_regression", "tlb_classifier", "sdm_regression", "sdm_classifier"]

    def __init__(self) -> None:
        self.reloaded = 0
        self.registry = {k: {"model": object(), "features": []} for k in self.KEYS}

    def reload(self):
        self.reloaded += 1
        return self.registry

    def info(self):
        return [
            {
                "model_key": key,
                "available": True,
                "path": f"/fake/{key}.joblib",
                "package_type": "FakeModel",
                "feature_count": 3,
                "features": ["plant_height", "ear_height", "shelling_percentage"],
                "error": None,
            }
            for key in self.KEYS
        ]

    @staticmethod
    def predict(df: pd.DataFrame, requested: set[str] | None = None) -> pd.DataFrame:
        requested = requested or set(FakeModelService.KEYS)
        d = df.copy()
        if "genotype" not in d.columns:
            d["genotype"] = [f"ROW_{i + 1}" for i in range(len(d))]
        out = pd.DataFrame({"genotype": d["genotype"].astype(str)})
        numeric = lambda c: pd.to_numeric(d.get(c, pd.Series(0, index=d.index)), errors="coerce").fillna(0)
        ph = numeric("plant_height")
        eh = numeric("ear_height")
        sh = numeric("shelling_percentage")
        base = ph * 10 + eh * 20 + sh * 5
        out["input_completeness"] = np.where(
            d.reindex(columns=[
                "days_to_50_percent_pollen_shedding", "days_to_50_percent_silking",
                "days_to_75_percent_dry_husk", "plant_height", "ear_height",
                "plant_stand", "shelling_percentage"
            ]).notna().all(axis=1),
            "FULL", "PARTIAL_INPUT_MODEL_IMPUTED"
        )
        if "yield" in requested:
            out["yield_model_status"] = "OK"
            out["yield_prediction_kg_ha"] = base
            out["yield_range_flag"] = "OK"
        if "tlb_regression" in requested:
            out["tlb_regression_model_status"] = "OK"
            out["tlb_score_prediction"] = 1 + (base % 8)
            out["tlb_score_range_flag"] = "OK"
        if "tlb_classifier" in requested:
            out["tlb_classifier_model_status"] = "OK"
            out["tlb_reaction_prediction"] = np.where(base % 2 == 0, "R", "S")
            out["tlb_classifier_class_probability"] = 0.8
        if "sdm_regression" in requested:
            out["sdm_regression_model_status"] = "OK"
            out["sdm_pdi_prediction"] = base % 100
            out["sdm_pdi_range_flag"] = "OK"
        if "sdm_classifier" in requested:
            out["sdm_classifier_model_status"] = "OK"
            out["sdm_reaction_prediction"] = np.where(base % 3 == 0, "MR", "MS")
            out["sdm_classifier_class_probability"] = 0.7
        return out.reset_index(drop=True)


class FakeDataService:
    def __init__(self):
        self.df = pd.DataFrame(
            [
                {"canonical_genotype": "G1", "domain": "yield", "experiment_id": "Y1", "experiment_no": 1, "trial_no": 1081, "source_section": "Yield", "location": "ZARS, Mandya", "season": "Rabi 2022-23", "year": "2022-23", "variable": "grain_yield", "canonical_trait": "grain_yield", "value_numeric": 10000},
                {"canonical_genotype": "G2", "domain": "yield", "experiment_id": "Y2", "experiment_no": 2, "trial_no": 1082, "source_section": "Yield", "location": "ZARS, Mandya", "season": "Rabi 2022-23", "year": "2022-23", "variable": "plant_height", "canonical_trait": "plant_height", "value_numeric": 220},
                {"canonical_genotype": "G1", "domain": "tlb", "experiment_id": "T1", "experiment_no": 1, "trial_no": 1099, "source_section": "TLB", "location": "ZARS, Mandya", "season": "Rabi 2022-23", "year": "2022-23", "variable": "tlb_disease_score", "canonical_trait": "tlb_disease_score", "value_numeric": 2},
                {"canonical_genotype": "G1", "domain": "sdm", "experiment_id": "S1", "experiment_no": 1, "trial_no": 1099, "source_section": "SDM", "location": "ZARS, Mandya", "season": "Rabi 2022-23", "year": "2022-23", "variable": "sdm_pdi", "canonical_trait": "sdm_pdi", "value_numeric": 3},
            ]
        )

    def load(self, domain):
        if domain not in {"yield", "tlb", "sdm", "multi_trait"}:
            return None, None
        sub = self.df[self.df["domain"] == domain].copy()
        if domain == "multi_trait":
            sub = self.df.copy()
        return sub, Path(f"/fake/{domain}.csv")

    def catalog(self):
        return [
            {"domain": d, "available": True, "path": f"/fake/{d}.csv", "rows": int(len(self.load(d)[0])), "columns": list(self.load(d)[0].columns)}
            for d in ["yield", "tlb", "sdm", "multi_trait"]
        ]

    @staticmethod
    def _search(df, query, columns):
        if not query:
            return df
        q = query.lower()
        mask = pd.Series(False, index=df.index)
        for c in columns:
            if c in df:
                mask |= df[c].astype(str).str.lower().str.contains(q, regex=False, na=False)
        return df.loc[mask]

    def genotypes(self, query, domain, limit, offset):
        domains = [domain] if domain in {"yield", "tlb", "sdm", "multi_trait"} else ["yield", "tlb", "sdm", "multi_trait"]
        vals = []
        for d in domains:
            df, _ = self.load(d)
            if df is None:
                continue
            sub = self._search(df, query, ["canonical_genotype"])
            vals.extend({"genotype": x, "domains": [d]} for x in sub["canonical_genotype"].astype(str).unique())
        merged = {}
        for x in vals:
            merged.setdefault(x["genotype"], {"genotype": x["genotype"], "domains": []})
            merged[x["genotype"]]["domains"].append(x["domains"][0])
        items = sorted(merged.values(), key=lambda r: r["genotype"])
        return {"total": len(items), "limit": limit, "offset": offset, "items": items[offset : offset + limit]}

    def genotype_detail(self, genotype):
        out = {"genotype": genotype, "domains": {}}
        for d in ["yield", "tlb", "sdm", "multi_trait"]:
            df, path = self.load(d)
            sub = df[df["canonical_genotype"].astype(str).str.casefold() == genotype.casefold()]
            if not sub.empty:
                out["domains"][d] = {"dataset": str(path), "rows": sub.to_dict(orient="records")}
        return out

    @staticmethod
    def search(df, query, cols):
        return FakeDataService._search(df, query, cols)

    @staticmethod
    def page(df, limit, offset):
        items = df.iloc[offset : offset + limit].where(pd.notna(df), None).to_dict(orient="records")
        return {"total": len(df), "limit": limit, "offset": offset, "items": items}


class FakeArtifactService:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        metric_files = {
            "YIELD_MODEL_COMPARISON.csv": "model,mae,rmse,r2\nRidge,10,20,0.5\n",
            "TLB_REGRESSION_MODEL_COMPARISON.csv": "model,mae,rmse,r2\nExtraTrees,1,2,0.5\n",
            "TLB_CLASSIFICATION_MODEL_COMPARISON.csv": "model,f1,balanced_accuracy\nRandomForest,0.7,0.8\n",
            "SDM_REGRESSION_MODEL_COMPARISON.csv": "model,mae,rmse,r2\nExtraTrees,2,3,0.4\n",
            "SDM_CLASSIFICATION_MODEL_COMPARISON.csv": "model,f1,balanced_accuracy\nRandomForest,0.6,0.7\n",
        }
        for name, content in metric_files.items():
            (self.root / name).write_text(content, encoding="utf-8")

    def clustering(self):
        return {"available": True, "files": {"GENOTYPE_CLUSTERS.csv": "/fake/GENOTYPE_CLUSTERS.csv"}}

    def clustering_data(self, filename, limit, offset):
        if filename not in {"GENOTYPE_CLUSTERS.csv", "PCA_SCORES.csv"}:
            return {"available": False, "filename": filename, "total": 0, "items": []}
        rows = [{"genotype": "G1", "cluster": 0}, {"genotype": "G2", "cluster": 1}]
        return {"available": True, "filename": filename, "path": f"/fake/{filename}", "total": len(rows), "limit": limit, "offset": offset, "items": rows[offset : offset + limit]}

    def weather_status(self):
        return {"available": True, "files": {"WEATHER_MODEL_STATUS.csv": "/fake/weather.csv"}}

    def explainability(self, model_key):
        if model_key not in {"yield", "tlb_regression", "tlb_classifier", "sdm_regression", "sdm_classifier"}:
            return {"available": False, "model_key": model_key, "items": []}
        return {"available": True, "model_key": model_key, "path": f"/fake/{model_key}.csv", "items": [{"feature": "plant_height", "importance_mean": 0.5}]}

    def _find_any(self, names):
        for name in names:
            p = self.root / name
            if p.exists():
                return p
        return None


def _make_client():
    return TestClient(app)


@pytest.fixture
def fake_services(monkeypatch):
    model = FakeModelService()
    data = FakeDataService()
    artifact = FakeArtifactService(Path(__file__).resolve().parent / ".fake_artifacts")
    monkeypatch.setattr(routes_models, "service", model)
    monkeypatch.setattr(routes_predict, "model_service", model)
    monkeypatch.setattr(routes_info, "model_service", model)
    monkeypatch.setattr(routes_data, "service", data)
    monkeypatch.setattr(routes_info, "_data", data)
    monkeypatch.setattr(routes_analytics, "service", artifact)
    monkeypatch.setattr(data_service_module, "DataService", lambda: data)
    return SimpleNamespace(model=model, data=data, artifact=artifact)


@pytest.fixture
def client(fake_services):
    with _make_client() as c:
        yield c
