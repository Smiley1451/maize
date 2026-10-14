from __future__ import annotations
from pathlib import Path
import json, re, warnings
import numpy as np
import pandas as pd
import joblib

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
MODELS = BASE/'models'

BASE_FEATURES=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
ALIASES={
    'pollen_shedding_days':'days_to_50_percent_pollen_shedding',
    'silking_days':'days_to_50_percent_silking',
    'dry_husk_days':'days_to_75_percent_dry_husk',
    'plant_height_cm':'plant_height',
    'ear_height_cm':'ear_height',
    'shelling_pct':'shelling_percentage',
    'plant_stand_000_per_ha':'plant_stand'
}


def norm_columns(df):
    d=df.copy()
    d.columns=[str(c).strip() for c in d.columns]
    if 'plant_stand_000_per_ha' in d.columns and 'plant_stand' not in d.columns:
        d['plant_stand']=pd.to_numeric(d['plant_stand_000_per_ha'],errors='coerce')*1000.0
    for a,b in ALIASES.items():
        if a in d.columns and b not in d.columns: d[b]=d[a]
    for c in BASE_FEATURES: 
        if c in d.columns: d[c]=pd.to_numeric(d[c],errors='coerce')
    d['silking_to_pollen_gap']=d.get('days_to_50_percent_silking',pd.Series(index=d.index,dtype=float))-d.get('days_to_50_percent_pollen_shedding',pd.Series(index=d.index,dtype=float))
    d['dry_husk_after_silking']=d.get('days_to_75_percent_dry_husk',pd.Series(index=d.index,dtype=float))-d.get('days_to_50_percent_silking',pd.Series(index=d.index,dtype=float))
    ph=pd.to_numeric(d.get('plant_height',pd.Series(index=d.index,dtype=float)),errors='coerce')
    eh=pd.to_numeric(d.get('ear_height',pd.Series(index=d.index,dtype=float)),errors='coerce')
    d['ear_height_ratio']=eh/ph.replace(0,np.nan)
    return d


def find_model(*names):
    locations=[MODELS,ROOT/'13_15_NEXT_PHASES'/'models',ROOT/'MAIZE_PHASES_13_15_DROP_IN'/'models',ROOT/'08_AUTOMATED_PIPELINE'/'models',ROOT/'08_AUTOMATED_PIPELINE'/'outputs'/'06_TUNING']
    for loc in locations:
        for name in names:
            p=loc/name
            if p.exists(): return p
    return None


def load_package(path):
    if path is None: return None
    try: return joblib.load(path)
    except Exception as e: raise RuntimeError(f'Could not load model package {path}: {e}')


def package_model(pkg):
    return pkg.get('model') if isinstance(pkg,dict) and 'model' in pkg else pkg


def package_features(pkg):
    if isinstance(pkg,dict) and pkg.get('features'): return list(pkg['features'])
    return BASE_FEATURES+['silking_to_pollen_gap','dry_husk_after_silking','ear_height_ratio']


def predict_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    d=norm_columns(df)
    out=pd.DataFrame(index=d.index)
    out['genotype']=d['genotype'].astype(str) if 'genotype' in d.columns else [f'ROW_{i+1}' for i in range(len(d))]
    expected_base=[c for c in BASE_FEATURES if c not in d.columns]
    out['input_completeness']='FULL' if not expected_base else 'PARTIAL_INPUT_MODEL_IMPUTED'
    out['missing_input_features']='' if not expected_base else '|'.join(expected_base)
    registry={}
    specs={
        'yield':('yield_advanced_selected.joblib','yield_tuned_random_forest.joblib'),
        'tlb_regression':('tlb_advanced_regression_selected.joblib','tlb_tuned_extratrees.joblib'),
        'tlb_classifier':('tlb_advanced_classifier_selected.joblib','tlb_tuned_random_forest_classifier.joblib'),
        'sdm_regression':('sdm_advanced_regression_selected.joblib','sdm_tuned_extratrees.joblib'),
        'sdm_classifier':('sdm_advanced_classifier_selected.joblib','sdm_tuned_random_forest_classifier.joblib')
    }
    for key,names in specs.items():
        p=find_model(*names); registry[key]=str(p) if p else ''
        out[f'{key}_model_status']= 'LOADED' if p else 'MODEL_UNAVAILABLE'
        if p is None: continue
        pkg=load_package(p); model=package_model(pkg); features=package_features(pkg)
        X=d.copy()
        for f in features:
            if f not in X.columns: X[f]=np.nan
        X=X[features]
        try:
            pred=model.predict(X)
        except Exception as e:
            out[f'{key}_model_status']='PREDICTION_ERROR'
            out[f'{key}_error']=str(e)
            continue
        if key=='yield':
            out['yield_prediction_kg_ha']=pd.to_numeric(pred,errors='coerce')
            out['yield_range_flag']=np.where((out['yield_prediction_kg_ha']<0)|(out['yield_prediction_kg_ha']>40000),'CHECK_RANGE','OK')
        elif key=='tlb_regression':
            out['tlb_score_prediction']=pd.to_numeric(pred,errors='coerce')
            out['tlb_score_range_flag']=np.where((out['tlb_score_prediction']<1)|(out['tlb_score_prediction']>9),'CHECK_RANGE','OK')
        elif key=='sdm_regression':
            out['sdm_pdi_prediction']=pd.to_numeric(pred,errors='coerce')
            out['sdm_pdi_range_flag']=np.where((out['sdm_pdi_prediction']<0)|(out['sdm_pdi_prediction']>100),'CHECK_RANGE','OK')
        else:
            out[key.replace('_classifier','_reaction_prediction')]=pd.Series(pred,index=d.index).astype(str)
            if hasattr(model,'predict_proba'):
                try:
                    prob=model.predict_proba(X); out[key.replace('_classifier','_class_probability')]=np.max(prob,axis=1)
                except Exception:
                    pass
    reg_rows=[{'model_key':k,'model_path':v} for k,v in registry.items()]
    pd.DataFrame(reg_rows).to_csv(BASE/'outputs'/'18_PREDICTION_ENGINE'/'MODEL_RUNTIME_REGISTRY.csv',index=False)
    return out
