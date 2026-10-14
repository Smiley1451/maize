from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.core.logging_setup import logger
from app.services.path_registry import MODEL_PATTERNS, find_named_model

BASE_FEATURES = [
    "days_to_50_percent_pollen_shedding",
    "days_to_50_percent_silking",
    "days_to_75_percent_dry_husk",
    "plant_height",
    "ear_height",
    "plant_stand",
    "shelling_percentage",
]
ENGINEERED = ["silking_to_pollen_gap", "dry_husk_after_silking", "ear_height_ratio"]


class ModelService:
    def __init__(self) -> None:
        self.registry: dict[str, dict[str, Any]] = {}
        self.reload()

    def reload(self) -> dict[str, dict[str, Any]]:
        self.registry = {}
        for key, names in MODEL_PATTERNS.items():
            path = find_named_model(names)
            entry: dict[str, Any] = {"path": path, "package": None, "features": [], "error": None}
            if path:
                try:
                    package = joblib.load(path)
                    model = package.get("model") if isinstance(package, dict) and "model" in package else package
                    features = package.get("features") if isinstance(package, dict) and package.get("features") else BASE_FEATURES + ENGINEERED
                    entry.update({"package": package, "model": model, "features": list(features)})
                    logger.info("MODEL LOADED: %s -> %s", key, path)
                except Exception as exc:
                    entry["error"] = str(exc)
                    logger.exception("MODEL LOAD FAILED: %s", key)
            self.registry[key] = entry
        return self.registry

    @staticmethod
    def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        d = df.copy()
        if "plant_stand_000_per_ha" in d.columns and "plant_stand" not in d.columns:
            d["plant_stand"] = pd.to_numeric(d["plant_stand_000_per_ha"], errors="coerce") * 1000.0
        aliases = {
            "pollen_shedding_days": "days_to_50_percent_pollen_shedding",
            "silking_days": "days_to_50_percent_silking",
            "dry_husk_days": "days_to_75_percent_dry_husk",
            "plant_height_cm": "plant_height",
            "ear_height_cm": "ear_height",
            "shelling_pct": "shelling_percentage",
        }
        for src, dst in aliases.items():
            if src in d.columns and dst not in d.columns:
                d[dst] = d[src]
        for c in BASE_FEATURES:
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")
        d["silking_to_pollen_gap"] = d.get("days_to_50_percent_silking", pd.Series(index=d.index, dtype=float)) - d.get("days_to_50_percent_pollen_shedding", pd.Series(index=d.index, dtype=float))
        d["dry_husk_after_silking"] = d.get("days_to_75_percent_dry_husk", pd.Series(index=d.index, dtype=float)) - d.get("days_to_50_percent_silking", pd.Series(index=d.index, dtype=float))
        ph = pd.to_numeric(d.get("plant_height", pd.Series(index=d.index, dtype=float)), errors="coerce")
        eh = pd.to_numeric(d.get("ear_height", pd.Series(index=d.index, dtype=float)), errors="coerce")
        d["ear_height_ratio"] = eh / ph.replace(0, np.nan)
        return d

    def info(self) -> list[dict[str, Any]]:
        out = []
        for key, e in self.registry.items():
            out.append({
                "model_key": key,
                "available": bool(e.get("path") and e.get("model")),
                "path": str(e["path"]) if e.get("path") else None,
                "package_type": type(e.get("model")).__name__ if e.get("model") else None,
                "feature_count": len(e.get("features") or []),
                "features": list(e.get("features") or []),
                "error": e.get("error"),
            })
        return out

    def _predict_one(self, key: str, df: pd.DataFrame) -> tuple[np.ndarray | None, str, list[str]]:
        e = self.registry.get(key, {})
        if not e.get("model"):
            return None, "MODEL_UNAVAILABLE", [e.get("error")] if e.get("error") else []
        X = self.prepare_dataframe(df)
        features = list(e.get("features") or BASE_FEATURES + ENGINEERED)
        for f in features:
            if f not in X.columns:
                X[f] = np.nan
        X = X[features]
        try:
            return np.asarray(e["model"].predict(X)), "OK", []
        except Exception as exc:
            logger.exception("PREDICTION FAILED: %s", key)
            return None, "PREDICTION_ERROR", [str(exc)]

    def predict(self, df: pd.DataFrame, requested: set[str] | None = None) -> pd.DataFrame:
        requested = requested or set(self.registry.keys())
        d = self.prepare_dataframe(df)
        out = pd.DataFrame(index=d.index)
        out["genotype"] = d["genotype"].astype(str) if "genotype" in d.columns else [f"ROW_{i+1}" for i in range(len(d))]
        out["input_completeness"] = np.where(d[BASE_FEATURES].notna().all(axis=1), "FULL", "PARTIAL_INPUT_MODEL_IMPUTED")

        for key in requested:
            pred, status, warnings = self._predict_one(key, d)
            out[f"{key}_model_status"] = status
            if warnings:
                out[f"{key}_warning"] = " | ".join(warnings)
            if pred is None:
                continue
            if key == "yield":
                out["yield_prediction_kg_ha"] = pd.to_numeric(pred, errors="coerce")
                out["yield_range_flag"] = np.where((out["yield_prediction_kg_ha"] < 0) | (out["yield_prediction_kg_ha"] > 40000), "CHECK_RANGE", "OK")
            elif key == "tlb_regression":
                out["tlb_score_prediction"] = pd.to_numeric(pred, errors="coerce")
                out["tlb_score_range_flag"] = np.where((out["tlb_score_prediction"] < 1) | (out["tlb_score_prediction"] > 9), "CHECK_RANGE", "OK")
            elif key == "sdm_regression":
                out["sdm_pdi_prediction"] = pd.to_numeric(pred, errors="coerce")
                out["sdm_pdi_range_flag"] = np.where((out["sdm_pdi_prediction"] < 0) | (out["sdm_pdi_prediction"] > 100), "CHECK_RANGE", "OK")
            elif key.endswith("_classifier"):
                col = key.replace("_classifier", "_reaction_prediction")
                out[col] = pd.Series(pred, index=d.index).astype(str)
                model = self.registry[key]["model"]
                if hasattr(model, "predict_proba"):
                    try:
                        prob = model.predict_proba(self.prepare_dataframe(d)[self.registry[key]["features"]])
                        out[key.replace("_classifier", "_class_probability")] = np.max(prob, axis=1)
                    except Exception:
                        pass
        return out.reset_index(drop=True)
