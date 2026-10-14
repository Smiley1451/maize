from __future__ import annotations
from pathlib import Path
from functools import lru_cache
import re
import joblib
import numpy as np
import pandas as pd
import httpx
from .config import PROJECT_ROOT, PHASE19_URL

BASE_FEATURES=[
    "days_to_50_percent_pollen_shedding","days_to_50_percent_silking","days_to_75_percent_dry_husk",
    "plant_height","ear_height","plant_stand","shelling_percentage"
]
ENGINEERED=["silking_to_pollen_gap","dry_husk_after_silking","ear_height_ratio"]
ALL_FEATURES=BASE_FEATURES+ENGINEERED
MODEL_NAME_HINTS={
    "yield":["yield_advanced_selected.joblib","YIELD_TUNED_RANDOM_FOREST.joblib","yield_tuned_random_forest.joblib","yield_ExtraTrees.joblib","yield_RandomForest.joblib"],
    "tlb_regression":["tlb_advanced_regression_selected.joblib","TLB_TUNED_EXTRATREES.joblib","tlb_tuned_extratrees.joblib","TLB_ExtraTrees.joblib"],
    "tlb_classifier":["tlb_advanced_classifier_selected.joblib","TLB_TUNED_RANDOM_FOREST_CLASSIFIER.joblib","tlb_tuned_random_forest_classifier.joblib","TLB_RandomForest_classifier.joblib"],
    "sdm_regression":["sdm_advanced_regression_selected.joblib","SDM_TUNED_EXTRATREES.joblib","sdm_tuned_extratrees.joblib","SDM_ExtraTrees.joblib"],
    "sdm_classifier":["sdm_advanced_classifier_selected.joblib","SDM_TUNED_RANDOM_FOREST_CLASSIFIER.joblib","sdm_tuned_random_forest_classifier.joblib","SDM_RandomForest_classifier.joblib"],
}
MODEL_ROOTS=["MAIZE_PHASES_16_18_DROP_IN/models","MAIZE_PHASES_13_15_DROP_IN/models","13_15_NEXT_PHASES/models","08_AUTOMATED_PIPELINE/models","08_AUTOMATED_PIPELINE/outputs/06_TUNING"]


def model_paths():
    for root in MODEL_ROOTS:
        p=PROJECT_ROOT/root
        if p.exists(): yield p


def find_model(*names):
    for root in model_paths():
        for name in names:
            p=root/name
            if p.exists(): return p
            try: return next(root.rglob(name))
            except StopIteration: pass
    return None


def available_models(include_metadata: bool = False):
    found=[]
    for p in PROJECT_ROOT.rglob("*.joblib"):
        rel=str(p.relative_to(PROJECT_ROOT)); kind="other"; low=p.name.casefold()
        for k,hints in MODEL_NAME_HINTS.items():
            if any(p.name.casefold()==h.casefold() for h in hints): kind=k; break
        rec={"path":rel,"filename":p.name,"kind":kind,"size_bytes":p.stat().st_size}
        if include_metadata:
            try:
                obj=joblib.load(p)
                rec["estimator_type"]=type(obj).__name__
                rec["n_features_in"]=getattr(obj,"n_features_in_",None)
                rec["steps"]=[x[0] for x in getattr(obj,"steps",[]) or []]
            except Exception as exc:
                rec["estimator_type"]=None; rec["n_features_in"]=None; rec["steps"]=[]; rec["load_note"]=f"not_loaded: {type(exc).__name__}"
        found.append(rec)
    return sorted(found,key=lambda x:x["path"])


def model_detail(path: str):
    target=(PROJECT_ROOT/path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)) or not target.exists() or target.suffix.lower()!='.joblib':
        return {"available":False,"path":path,"error":"model artifact not found or invalid"}
    try:
        obj=joblib.load(target)
        return {"available":True,"path":str(target.relative_to(PROJECT_ROOT)),"estimator_type":type(obj).__name__,
                "n_features_in":getattr(obj,"n_features_in_",None),"steps":[x[0] for x in getattr(obj,"steps",[]) or []]}
    except Exception as exc:
        return {"available":False,"path":str(target.relative_to(PROJECT_ROOT)),"error":str(exc)}

_HTTP_HEALTH_CACHE=None

def phase19_get(path, params=None):
    try:
        r=httpx.get(PHASE19_URL+path,params=params,timeout=0.75)
        if r.status_code < 500: return r.json()
    except Exception: return None
    return None


def phase19_health():
    global _HTTP_HEALTH_CACHE
    if _HTTP_HEALTH_CACHE is not None: return _HTTP_HEALTH_CACHE
    r=phase19_get("/health")
    _HTTP_HEALTH_CACHE=r if r is not None else {"status":"offline","message":"Phase 19 API is not running"}
    return _HTTP_HEALTH_CACHE


def _find_csv(*names):
    for root in model_paths():
        for name in names:
            p=root/name
            if p.exists(): return p
            try: return next(root.rglob(name))
            except StopIteration: pass
    # Metrics/explainability may be stored in phase output folders rather than model folders.
    for name in names:
        try:
            return next(p for p in PROJECT_ROOT.rglob(name) if p.is_file())
        except StopIteration:
            pass
    return None


def _csv_payload(path):
    if not path: return {"available":False,"items":[]}
    try:
        df=pd.read_csv(path,low_memory=False)
        return {"available":True,"path":str(path.relative_to(PROJECT_ROOT)),"items":df.where(pd.notna(df),None).to_dict(orient="records")}
    except Exception as exc: return {"available":False,"path":str(path),"error":str(exc),"items":[]}


def get_model_metrics(domain,kind="regression"):
    names={
        ("yield","regression"): ["YIELD_MODEL_COMPARISON.csv","TUNING_RESULTS.csv","ADVANCED_YIELD_MODEL_COMPARISON.csv"],
        ("tlb","regression"): ["TLB_REGRESSION_MODEL_COMPARISON.csv","DISEASE_TUNING_RESULTS.csv"],
        ("tlb","classification"): ["TLB_CLASSIFICATION_MODEL_COMPARISON.csv","DISEASE_CLASSIFICATION_TUNING_RESULTS.csv"],
        ("sdm","regression"): ["SDM_REGRESSION_MODEL_COMPARISON.csv","DISEASE_TUNING_RESULTS.csv"],
        ("sdm","classification"): ["SDM_CLASSIFICATION_MODEL_COMPARISON.csv","DISEASE_CLASSIFICATION_TUNING_RESULTS.csv"],
    }.get((domain,kind),[])
    local=_csv_payload(_find_csv(*names))
    local.update({"domain":domain,"kind":kind,"source":"local_artifact"})
    return local


def get_explainability(key):
    name_map={
        "yield":["YIELD_PERMUTATION_IMPORTANCE.csv","YIELD_REGRESSION_PERMUTATION_IMPORTANCE.csv"],
        "tlb_regression":["TLB_PERMUTATION_IMPORTANCE.csv","TLB_REGRESSION_PERMUTATION_IMPORTANCE.csv"],
        "tlb_classifier":["TLB_CLASSIFIER_PERMUTATION_IMPORTANCE.csv","TLB_CLASSIFICATION_PERMUTATION_IMPORTANCE.csv"],
        "sdm_regression":["SDM_PERMUTATION_IMPORTANCE.csv","SDM_REGRESSION_PERMUTATION_IMPORTANCE.csv"],
        "sdm_classifier":["SDM_CLASSIFIER_PERMUTATION_IMPORTANCE.csv","SDM_CLASSIFICATION_PERMUTATION_IMPORTANCE.csv"],
    }.get(key,[])
    local=_csv_payload(_find_csv(*name_map)); local.update({"model_key":key,"source":"local_artifact"}); return local

def _prepare(df):
    d=df.copy()
    aliases={
        "pollen_shedding_days":"days_to_50_percent_pollen_shedding","silking_days":"days_to_50_percent_silking",
        "dry_husk_days":"days_to_75_percent_dry_husk","plant_height_cm":"plant_height","ear_height_cm":"ear_height",
        "shelling_pct":"shelling_percentage","plant_stand_000_per_ha":"plant_stand"
    }
    if "plant_stand_000_per_ha" in d.columns and "plant_stand" not in d.columns:
        d["plant_stand"]=pd.to_numeric(d["plant_stand_000_per_ha"],errors="coerce")*1000.0
    for a,b in aliases.items():
        if a in d.columns and b not in d.columns: d[b]=d[a]
    for c in BASE_FEATURES: d[c]=pd.to_numeric(d.get(c),errors="coerce") if c in d.columns else np.nan
    d["silking_to_pollen_gap"]=d["days_to_50_percent_silking"]-d["days_to_50_percent_pollen_shedding"]
    d["dry_husk_after_silking"]=d["days_to_75_percent_dry_husk"]-d["days_to_50_percent_silking"]
    d["ear_height_ratio"]=d["ear_height"]/d["plant_height"].replace(0,np.nan)
    return d


def local_predict(payload:dict, domains=None):
    domains=domains or ["yield","tlb_regression","tlb_classifier","sdm_regression","sdm_classifier"]
    row=dict(payload); df=_prepare(pd.DataFrame([row])); result={"status":"ok","source":"local_model_loader","genotype":str(row.get("genotype", "ROW_1"))}
    specs={
        "yield":MODEL_NAME_HINTS["yield"],"tlb_regression":MODEL_NAME_HINTS["tlb_regression"],"tlb_classifier":MODEL_NAME_HINTS["tlb_classifier"],
        "sdm_regression":MODEL_NAME_HINTS["sdm_regression"],"sdm_classifier":MODEL_NAME_HINTS["sdm_classifier"]
    }
    for key in domains:
        p=find_model(*specs.get(key,[]))
        if p is None:
            result[key]={"status":"MODEL_UNAVAILABLE"}; continue
        try:
            obj=joblib.load(p); model=obj.get("model") if isinstance(obj,dict) and "model" in obj else obj
            feats=list(obj.get("features",ALL_FEATURES)) if isinstance(obj,dict) else ALL_FEATURES
            X=df.copy()
            for f in feats:
                if f not in X.columns: X[f]=np.nan
            pred=model.predict(X[feats])[0]
            item={"status":"OK","model_file":str(p.relative_to(PROJECT_ROOT)),"prediction":str(pred)}
            if key=="yield": item["prediction_kg_ha"]=float(pred)
            if key=="tlb_regression": item["score"]=float(pred)
            if key=="sdm_regression": item["pdi"]=float(pred)
            if key.endswith("classifier"):
                item["reaction"]=str(pred)
                if hasattr(model,"predict_proba"):
                    probs=model.predict_proba(X[feats])[0]
                    item["class_probability"]=float(np.max(probs))
            result[key]=item
        except Exception as exc:
            result[key]={"status":"PREDICTION_ERROR","model_file":str(p.relative_to(PROJECT_ROOT)),"error":str(exc)}
    return result
