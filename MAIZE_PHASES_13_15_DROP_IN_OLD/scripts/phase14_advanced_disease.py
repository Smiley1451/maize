from __future__ import annotations
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_13_15 import *

from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix
from sklearn.base import clone
from joblib import dump

warnings.filterwarnings("ignore", message=r"y_pred contains classes not in y_true")
warnings.filterwarnings("ignore", message=r"A single label was found")

BASE11 = ROOT/'10_12_NEXT_PHASES'/'outputs'/'PHASE_11_PRODUCTION_DATASETS'
OUT = phase_out('PHASE_14_ADVANCED_DISEASE')

FEATURES_BASE=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
FEATURES=FEATURES_BASE+['silking_to_pollen_gap','dry_husk_after_silking','ear_height_ratio']


def prepare(path, disease, target, cls):
    p=BASE11/path
    if not p.exists(): raise FileNotFoundError(f'Missing upstream input: {p}')
    d=pd.read_csv(p)
    need=FEATURES_BASE+['genotype_id','canonical_genotype_candidate','experiment_id',target,cls]
    missing=[c for c in need if c not in d.columns]
    if missing: raise ValueError(f'{disease} dataset missing columns: {missing}')
    d=d[d['production_eligible'].astype(str).str.lower().isin(['true','1','yes'])].copy() if 'production_eligible' in d.columns else d.copy()
    d=d[d['usable_link'].astype(str).str.lower().isin(['true','1','yes'])].copy() if 'usable_link' in d.columns else d.copy()
    for c in FEATURES_BASE: d[c]=clean_num(d[c])
    d['silking_to_pollen_gap']=d['days_to_50_percent_silking']-d['days_to_50_percent_pollen_shedding']
    d['dry_husk_after_silking']=d['days_to_75_percent_dry_husk']-d['days_to_50_percent_silking']
    d['ear_height_ratio']=d['ear_height']/d['plant_height'].replace(0,np.nan)
    d['target_value_numeric']=clean_num(d[target])
    d['class_label']=d[cls].astype(str).str.strip().str.upper()
    d['genotype_id']=d['genotype_id'].astype(str)
    return d


def class_support(d, disease):
    counts=d['class_label'].value_counts().rename_axis('class_label').reset_index(name='n')
    counts['disease']=disease
    counts['pct']=100*counts.n/counts.n.sum()
    counts['min_class_n']=counts.n.min()
    counts['min_to_max_ratio']=counts.n.min()/max(counts.n.max(),1)
    counts['support_flag']=np.where((counts['min_class_n']<5)|(counts['min_to_max_ratio']<0.10),'LOW_SUPPORT','OK')
    save(counts, OUT/f'{disease}_CLASS_SUPPORT.csv')
    return counts


def reg_models():
    return {
      'Ridge':Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',Ridge(alpha=10.0))]),
      'RandomForest':Pipeline([('imputer',SimpleImputer(strategy='median')),('model',RandomForestRegressor(n_estimators=500,max_features='sqrt',min_samples_leaf=2,random_state=SEED,n_jobs=1))]),
      'ExtraTrees':Pipeline([('imputer',SimpleImputer(strategy='median')),('model',ExtraTreesRegressor(n_estimators=500,max_features=1.0,random_state=SEED,n_jobs=1))]),
      'HistGradientBoosting':Pipeline([('imputer',SimpleImputer(strategy='median')),('model',HistGradientBoostingRegressor(max_iter=300,learning_rate=0.04,max_leaf_nodes=12,l2_regularization=1.0,random_state=SEED))])
    }

def cls_models():
    return {
      'LogisticRegression':Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(max_iter=2000,class_weight='balanced',C=1.0))]),
      'SVM':Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',SVC(C=1.0,kernel='rbf',class_weight='balanced'))]),
      'RandomForest':Pipeline([('imputer',SimpleImputer(strategy='median')),('model',RandomForestClassifier(n_estimators=500,max_features='sqrt',min_samples_leaf=2,class_weight='balanced_subsample',random_state=SEED,n_jobs=1))]),
      'ExtraTrees':Pipeline([('imputer',SimpleImputer(strategy='median')),('model',ExtraTreesClassifier(n_estimators=500,max_features='sqrt',class_weight='balanced',random_state=SEED,n_jobs=1))]),
      'HistGradientBoosting':Pipeline([('imputer',SimpleImputer(strategy='median')),('model',HistGradientBoostingClassifier(max_iter=250,learning_rate=0.05,max_leaf_nodes=12,l2_regularization=1.0,random_state=SEED))])
    }


def evaluate_reg(d,disease):
    X=d[FEATURES]; y=d['target_value_numeric'].to_numpy(float); groups=d['genotype_id'].to_numpy(str)
    valid=np.isfinite(y); X=X.loc[valid].reset_index(drop=True); y=y[valid]; groups=groups[valid]
    if len(d.groupby('genotype_id'))<5: raise ValueError(f'Not enough genotype groups for {disease} regression')
    gkf=GroupKFold(5); rows=[]; preds=[]; models=reg_models()
    for name,model in models.items():
        log(f'TRAINING {disease} ADVANCED {name} regression model - grouped CV...')
        fs=[]
        for fold,(tr,te) in enumerate(gkf.split(X,y,groups=groups),1):
            m=clone(model); m.fit(X.iloc[tr],y[tr]); p=m.predict(X.iloc[te])
            fs.append((mean_absolute_error(y[te],p),np.sqrt(mean_squared_error(y[te],p)),r2_score(y[te],p) if len(np.unique(y[te]))>1 else np.nan))
            preds += [{'disease':disease,'model':name,'fold':fold,'actual':float(a),'predicted':float(pp),'genotype_id':groups[i]} for i,pp,a in zip(te,p,y[te])]
        rows.append({'disease':disease,'model':name,'folds':5,'n':len(y),'mean_MAE':np.mean([x[0] for x in fs]),'mean_RMSE':np.mean([x[1] for x in fs]),'mean_R2':np.nanmean([x[2] for x in fs])})
        log(f'{disease} ADVANCED {name} regression model done')
    comp=pd.DataFrame(rows).sort_values(['mean_RMSE','mean_MAE']).reset_index(drop=True)
    save(comp,OUT/f'{disease}_REGRESSION_COMPARISON.csv'); save(pd.DataFrame(preds),OUT/f'{disease}_REGRESSION_FOLD_PREDICTIONS.csv')
    selected=comp.iloc[0].model; final=clone(models[selected]); final.fit(X,y); path=MODELS/f'{disease.lower()}_advanced_regression_selected.joblib'; dump({'model':final,'features':FEATURES,'target':str('target_value_numeric'),'disease':disease,'model_name':selected},path)
    save(pd.DataFrame([{'disease':disease,'selected_model':selected,'model_file':str(path.relative_to(BASE)),'selection_rule':'lowest GroupKFold mean RMSE, then MAE'}]),OUT/f'{disease}_SELECTED_REGRESSION.csv')


def evaluate_cls(d,disease):
    work=d.dropna(subset=['class_label']).copy(); y=work['class_label'].astype(str).to_numpy(); X=work[FEATURES]; groups=work['genotype_id'].astype(str).to_numpy()
    if len(np.unique(y))<2: raise ValueError(f'{disease} classification has fewer than 2 classes')
    gkf=GroupKFold(5); rows=[]; preds=[]; cms=[]; models=cls_models()
    for name,model in models.items():
        log(f'TRAINING {disease} ADVANCED {name} classification model - grouped CV...')
        fs=[]
        for fold,(tr,te) in enumerate(gkf.split(X,y,groups=groups),1):
            m=clone(model); m.fit(X.iloc[tr],y[tr]); p=m.predict(X.iloc[te])
            labels=sorted(set(y[tr])|set(y[te])|set(p))
            cm=confusion_matrix(y[te],p,labels=labels)
            fs.append((accuracy_score(y[te],p),balanced_accuracy_score(y[te],p),f1_score(y[te],p,average='macro',zero_division=0)))
            cms.append({'disease':disease,'model':name,'fold':fold,'labels':'|'.join(labels),'confusion_matrix':cm.tolist()})
            preds += [{'disease':disease,'model':name,'fold':fold,'actual_class':str(a),'predicted_class':str(pp),'genotype_id':groups[i]} for i,pp,a in zip(te,p,y[te])]
        rows.append({'disease':disease,'model':name,'folds':5,'n':len(y),'mean_accuracy':np.mean([x[0] for x in fs]),'mean_balanced_accuracy':np.mean([x[1] for x in fs]),'mean_f1_macro':np.mean([x[2] for x in fs])})
        log(f'{disease} ADVANCED {name} classification model done')
    comp=pd.DataFrame(rows).sort_values(['mean_f1_macro','mean_balanced_accuracy'],ascending=[False,False]).reset_index(drop=True)
    save(comp,OUT/f'{disease}_CLASSIFICATION_COMPARISON.csv'); save(pd.DataFrame(preds),OUT/f'{disease}_CLASSIFICATION_FOLD_PREDICTIONS.csv'); save(pd.DataFrame(cms),OUT/f'{disease}_CONFUSION_MATRICES.csv')
    selected=comp.iloc[0].model; final=clone(models[selected]); final.fit(X,y); path=MODELS/f'{disease.lower()}_advanced_classifier_selected.joblib'; dump({'model':final,'features':FEATURES,'target':'class_label','disease':disease,'model_name':selected,'classes':sorted(np.unique(y))},path)
    save(pd.DataFrame([{'disease':disease,'selected_model':selected,'model_file':str(path.relative_to(BASE)),'selection_rule':'highest GroupKFold macro-F1, then balanced accuracy'}]),OUT/f'{disease}_SELECTED_CLASSIFICATION.csv')


def main():
    log('='*62); log('PHASE 14: ADVANCED TLB + SDM DISEASE MODELING'); log('='*62)
    for disease,fn,target,cls in [('TLB','TLB_PRODUCTION_STRICT.csv','tlb_disease_score','tlb_reaction'),('SDM','SDM_PRODUCTION_STRICT.csv','sdm_pdi','sdm_reaction')]:
        d=prepare(fn,disease,target,cls)
        save(d,OUT/f'{disease}_ADVANCED_READY.csv')
        support=class_support(d,disease)
        flag=support['support_flag'].iloc[0] if not support.empty else 'NO_DATA'
        log(f'{disease} ADVANCED DATA: {len(d)} rows, {d.genotype_id.nunique()} genotypes, class support flag={flag}')
        evaluate_reg(d,disease); evaluate_cls(d,disease)
    (OUT/'PHASE14_SUMMARY.txt').write_text('PHASE 14 DONE\nAdvanced TLB and SDM regression + classification completed.\nClassification class-support audits are included; severe imbalance means generalization must be interpreted cautiously.\n',encoding='utf-8')
    log('PHASE 14 DONE: Advanced disease modeling complete')
if __name__=='__main__': main()
