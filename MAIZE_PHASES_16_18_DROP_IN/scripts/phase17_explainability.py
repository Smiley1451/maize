from __future__ import annotations
from pathlib import Path
import sys, warnings
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_16_18 import *

from sklearn.base import clone
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold
from sklearn.metrics import mean_absolute_error, f1_score, balanced_accuracy_score
import matplotlib.pyplot as plt
import joblib

OUT17 = phase_out('17_EXPLAINABILITY')
REPEATS = int(cfg().get('explainability',{}).get('permutation_repeats',10))

TARGETS = [
    ('yield','regression','yield_advanced_selected.joblib','YIELD_ADVANCED_READY.csv','yield_kg_ha_corrected'),
    ('TLB','regression','tlb_advanced_regression_selected.joblib','TLB_ADVANCED_READY.csv','target_value_numeric'),
    ('SDM','regression','sdm_advanced_regression_selected.joblib','SDM_ADVANCED_READY.csv','target_value_numeric'),
    ('TLB','classification','tlb_advanced_classifier_selected.joblib','TLB_ADVANCED_READY.csv','class_label'),
    ('SDM','classification','sdm_advanced_classifier_selected.joblib','SDM_ADVANCED_READY.csv','class_label'),
]


def model_path(fname):
    return find_model_file([fname])


def data_path(disease, fname):
    if disease=='yield':
        b=find_phase13_base()
        return b/fname if b else None
    b=find_phase14_base()
    return b/fname if b else None


def choose_splits(X,y,groups,classification=False):
    ng=len(np.unique(groups))
    n=min(5,ng)
    if n<2: return []
    if classification:
        try:
            _,counts=np.unique(y,return_counts=True)
            n=min(n,int(counts.min()))
            if n<2: return []
            cv=StratifiedGroupKFold(n_splits=n,shuffle=True,random_state=SEED)
            return list(cv.split(X,y,groups=groups))
        except Exception:
            pass
    cv=GroupKFold(n_splits=n)
    return list(cv.split(X,y,groups=groups))


def perm_importance(target_name, task, package_file, dataset_file, target):
    mp=model_path(package_file)
    dp=data_path(target_name, dataset_file)
    if mp is None or dp is None or not dp.exists():
        return {'status':'SKIPPED','reason':f'Missing model or dataset: model={mp}, dataset={dp}'}
    package=joblib.load(mp)
    model=package['model'] if isinstance(package,dict) and 'model' in package else package
    features=(package.get('features') if isinstance(package,dict) else None) or []
    d=pd.read_csv(dp)
    if not features:
        features=[c for c in ['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage','silking_to_pollen_gap','dry_husk_after_silking','ear_height_ratio'] if c in d.columns]
    missing=[f for f in features if f not in d.columns]
    if missing: return {'status':'SKIPPED','reason':f'Missing feature columns: {missing}'}
    if target not in d.columns or 'genotype_id' not in d.columns: return {'status':'SKIPPED','reason':'Missing target/genotype_id columns'}
    work=d.copy(); work=work[pd.notna(work[target])].copy(); X=work[features].copy(); y=work[target].to_numpy(); groups=work['genotype_id'].astype(str).to_numpy()
    if len(work)<4 or len(np.unique(groups))<2: return {'status':'SKIPPED','reason':'Too little data/groups'}
    splits=choose_splits(X,y,groups,task=='classification')
    if not splits: return {'status':'SKIPPED','reason':'Safe grouped CV could not be formed'}
    rows=[]; pred_rows=[]
    rng=np.random.default_rng(SEED)
    for fold,(tr,te) in enumerate(splits,1):
        m=clone(model)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m.fit(X.iloc[tr],y[tr])
            p=m.predict(X.iloc[te])
        if task=='regression':
            base=mean_absolute_error(y[te],p)
            metric='MAE'; higher_is_better=False
        else:
            base=f1_score(y[te],p,average='macro',zero_division=0)
            metric='F1_macro'; higher_is_better=True
        pred_rows.extend([{'domain':target_name,'task':task,'fold':fold,'genotype_id':groups[i],'actual':str(y[i]) if task!='regression' else float(y[i]),'predicted':str(pp) if task!='regression' else float(pp),'absolute_error':abs(float(y[i])-float(pp)) if task=='regression' else np.nan} for i,pp in zip(te,p)])
        for feature in features:
            changes=[]
            base_te=X.iloc[te].copy()
            for rep in range(REPEATS):
                perm=base_te.copy(); vals=perm[feature].to_numpy(copy=True); rng.shuffle(vals); perm[feature]=vals
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    pp=m.predict(perm)
                score=mean_absolute_error(y[te],pp) if task=='regression' else f1_score(y[te],pp,average='macro',zero_division=0)
                changes.append((score-base) if task=='regression' else (base-score))
            rows.append({'domain':target_name,'task':task,'model_name':package.get('model_name','unknown') if isinstance(package,dict) else 'unknown','fold':fold,'feature':feature,'importance_mean':float(np.mean(changes)),'importance_std':float(np.std(changes)),'metric':metric})
    imp=pd.DataFrame(rows)
    grouped=imp.groupby(['domain','task','feature'],as_index=False).agg(importance_mean=('importance_mean','mean'),importance_std=('importance_mean','std'),folds=('fold','nunique'),metric=('metric','first'))
    prefix=target_name.lower()+'_'+task
    save(grouped.sort_values('importance_mean',ascending=False),OUT17/f'{prefix.upper()}_PERMUTATION_IMPORTANCE.csv')
    save(pd.DataFrame(pred_rows),OUT17/f'{prefix.upper()}_PREDICTIONS.csv')
    if not grouped.empty:
        top=grouped.sort_values('importance_mean',ascending=False).head(15).sort_values('importance_mean')
        plt.figure(figsize=(8,5)); plt.barh(top['feature'],top['importance_mean']); plt.xlabel(f'Permutation importance ({metric})'); plt.title(f'{target_name} {task} explainability'); plt.tight_layout(); plt.savefig(OUT17/f'{prefix.upper()}_IMPORTANCE.png',dpi=160); plt.close()
    return {'status':'DONE','domain':target_name,'task':task,'rows':len(work),'folds':len(splits),'features':len(features),'model':str(mp)}


def main():
    log('='*62); log('PHASE 17: MODEL EXPLAINABILITY + ERROR ANALYSIS'); log('='*62)
    statuses=[]
    for domain,task,mfile,dfile,target in TARGETS:
        log(f'ANALYZING {domain} {task} model explainability...')
        r=perm_importance(domain,task,mfile,dfile,target); statuses.append(r)
        log(f'{domain} {task} explainability status: {r.get("status")}')
    save(pd.DataFrame(statuses), OUT17/'EXPLAINABILITY_STATUS.csv')
    # Consolidated error summary from prediction files created above.
    errs=[]
    for p in OUT17.glob('*_PREDICTIONS.csv'):
        d=pd.read_csv(p)
        if 'absolute_error' in d.columns and d['absolute_error'].notna().any():
            errs.append({'file':p.name,'rows':len(d),'mean_absolute_error':float(d['absolute_error'].mean()),'median_absolute_error':float(d['absolute_error'].median())})
    save(pd.DataFrame(errs), OUT17/'ERROR_ANALYSIS_SUMMARY.csv')
    (OUT17/'PHASE17_SUMMARY.txt').write_text('Phase 17 completed with grouped permutation explainability. Skipped model targets are recorded explicitly in EXPLAINABILITY_STATUS.csv.\n',encoding='utf-8')
    log('PHASE 17 DONE: explainability and error-analysis artifacts created.')

if __name__=='__main__': main()
