from __future__ import annotations
import sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common_13_15 import *

from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.base import clone
from joblib import dump

INPUT = ROOT / '10_12_NEXT_PHASES' / 'outputs' / 'PHASE_11_PRODUCTION_DATASETS' / 'YIELD_PRODUCTION_STRICT.csv'
OUT = phase_out('PHASE_13_ADVANCED_YIELD')

BASE_FEATURES = [
    'days_to_50_percent_pollen_shedding','days_to_50_percent_silking',
    'days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage'
]
ENGINEERED = ['silking_to_pollen_gap','dry_husk_after_silking','ear_height_ratio']


def xgb_model():
    try:
        from xgboost import XGBRegressor
        return XGBRegressor(
            n_estimators=350, max_depth=4, learning_rate=0.04,
            subsample=0.85, colsample_bytree=0.85, reg_lambda=2.0,
            objective='reg:squarederror', random_state=SEED, n_jobs=1
        )
    except Exception as e:
        log(f'XGBoost unavailable in this environment; skipping. Reason: {type(e).__name__}: {e}')
        return None


def build_dataset():
    if not INPUT.exists():
        raise FileNotFoundError(f'Missing upstream input: {INPUT}')
    d = pd.read_csv(INPUT)
    required = ['genotype_id','canonical_genotype_candidate','experiment_id','category','unit','value'] + BASE_FEATURES
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f'Yield dataset is missing columns: {missing}')
    d = d.copy()
    rows=[]
    for _, r in d.iterrows():
        y, method = yield_correct(r.get('value'), r.get('unit'))
        # Strong audit: compare Phase-11 derived value where present.
        prior = pd.to_numeric(r.get('yield_kg_ha'), errors='coerce')
        discrepancy = np.nan
        if pd.notna(y) and pd.notna(prior):
            discrepancy = abs(prior - y)
        rows.append((y, method, prior, discrepancy))
    d[['yield_kg_ha_corrected','yield_conversion_method_corrected','phase11_yield_kg_ha','phase11_target_abs_diff']] = rows
    d = d[pd.notna(d.yield_kg_ha_corrected)].copy()
    for c in BASE_FEATURES:
        d[c] = clean_num(d[c])
    d['silking_to_pollen_gap'] = d['days_to_50_percent_silking'] - d['days_to_50_percent_pollen_shedding']
    d['dry_husk_after_silking'] = d['days_to_75_percent_dry_husk'] - d['days_to_50_percent_silking']
    d['ear_height_ratio'] = d['ear_height'] / d['plant_height'].replace(0, np.nan)
    d['experiment_mean_kg_ha'] = d.groupby('experiment_id').yield_kg_ha_corrected.transform('mean')
    d['yield_index_pct_experiment_mean'] = 100.0 * d['yield_kg_ha_corrected'] / d['experiment_mean_kg_ha']
    check_medians = d[d['category'].astype(str).str.lower().eq('check')].groupby('experiment_id').yield_kg_ha_corrected.median()
    d['check_median_kg_ha'] = d['experiment_id'].map(check_medians)
    d['yield_vs_check_pct'] = 100.0 * d['yield_kg_ha_corrected'] / d['check_median_kg_ha']
    d['name_key'] = d['canonical_genotype_candidate'].map(norm_name)
    d['genotype_id'] = d['genotype_id'].astype(str)
    save(d, OUT/'YIELD_ADVANCED_READY.csv')
    audit_cols=['experiment_id','canonical_genotype_candidate','unit','value','phase11_yield_kg_ha','yield_kg_ha_corrected','yield_conversion_method_corrected','phase11_target_abs_diff']
    save(d[audit_cols].sort_values(['experiment_id','canonical_genotype_candidate']), OUT/'YIELD_UNIT_REAUDIT.csv')
    # Summaries for experiment-level normalization.
    save(d.groupby('experiment_id').agg(n=('genotype_id','size'),mean_yield_kg_ha=('yield_kg_ha_corrected','mean'),median_yield_kg_ha=('yield_kg_ha_corrected','median')).reset_index(), OUT/'YIELD_EXPERIMENT_SUMMARY.csv')
    return d


def evaluate(d):
    features = BASE_FEATURES + ENGINEERED
    X = d[features].copy()
    y = d['yield_kg_ha_corrected'].to_numpy(float)
    groups = d['genotype_id'].astype(str).to_numpy()
    gkf = GroupKFold(n_splits=5)
    models = {
        'Ridge': Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',Ridge(alpha=10.0))]),
        'RandomForest': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',RandomForestRegressor(n_estimators=500,max_features='sqrt',min_samples_leaf=2,random_state=SEED,n_jobs=1))]),
        'ExtraTrees': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',ExtraTreesRegressor(n_estimators=500,max_features=1.0,min_samples_leaf=1,random_state=SEED,n_jobs=1))]),
        'HistGradientBoosting': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',HistGradientBoostingRegressor(max_iter=300,learning_rate=0.04,max_leaf_nodes=12,l2_regularization=1.0,random_state=SEED))]),
    }
    xm=xgb_model()
    if xm is not None:
        models['XGBoost']=Pipeline([('imputer',SimpleImputer(strategy='median')),('model',xm)])
    rows=[]
    pred_rows=[]
    for name, model in models.items():
        log(f'TRAINING ADVANCED YIELD {name} model - grouped CV...')
        fold_metrics=[]
        for fold,(tr,te) in enumerate(gkf.split(X,y,groups=groups),1):
            m=clone(model); m.fit(X.iloc[tr], y[tr]); p=m.predict(X.iloc[te])
            mae=mean_absolute_error(y[te],p); rmse=np.sqrt(mean_squared_error(y[te],p));
            r2=r2_score(y[te],p) if len(np.unique(y[te]))>1 else np.nan
            fold_metrics.append({'fold':fold,'model':name,'n':len(te),'MAE':mae,'RMSE':rmse,'R2':r2})
            pred_rows.extend([{'model':name,'fold':fold,'genotype_id':groups[i],'actual_yield_kg_ha':y[i],'predicted_yield_kg_ha':float(pp)} for i,pp in zip(te,p)])
        fdf=pd.DataFrame(fold_metrics); rows.append({'model':name,'folds':5,'n':len(d),'mean_MAE':fdf.MAE.mean(),'mean_RMSE':fdf.RMSE.mean(),'mean_R2':fdf.R2.mean()});
        log(f'ADVANCED YIELD {name} model done')
    comp=pd.DataFrame(rows).sort_values(['mean_RMSE','mean_MAE']).reset_index(drop=True)
    save(comp, OUT/'ADVANCED_YIELD_MODEL_COMPARISON.csv')
    save(pd.DataFrame(pred_rows), OUT/'ADVANCED_YIELD_FOLD_PREDICTIONS.csv')
    selected=comp.iloc[0].model
    # Fit selected candidate on all eligible advanced data.
    final_model=clone(models[selected]); final_model.fit(X,y)
    package={'model':final_model,'features':features,'target':'yield_kg_ha_corrected','model_name':selected,'seed':SEED,'source_dataset':str(OUT/'YIELD_ADVANCED_READY.csv')}
    model_path=MODELS/'yield_advanced_selected.joblib'; dump(package, model_path)
    save(pd.DataFrame([{'selected_model':selected,'model_file':str(model_path.relative_to(BASE)),'selection_rule':'lowest GroupKFold mean RMSE, then MAE'}]), OUT/'SELECTED_YIELD_MODEL.csv')
    # Permutation-style importances are deferred to Phase 17, but a simple coefficient/tree importance is useful now.
    return selected


def main():
    log('='*62); log('PHASE 13: ADVANCED YIELD MODELING'); log('='*62)
    d=build_dataset(); log(f'ADVANCED YIELD DATA: {len(d)} rows, {d.genotype_id.nunique()} genotypes, {d.experiment_id.nunique()} experiments')
    selected=evaluate(d)
    (OUT/'PHASE13_SUMMARY.txt').write_text(f'PHASE 13 DONE\nSelected model: {selected}\nRows: {len(d)}\nGenotypes: {d.genotype_id.nunique()}\nExperiments: {d.experiment_id.nunique()}\n',encoding='utf-8')
    log('PHASE 13 DONE: Advanced yield modeling complete')

if __name__=='__main__': main()
