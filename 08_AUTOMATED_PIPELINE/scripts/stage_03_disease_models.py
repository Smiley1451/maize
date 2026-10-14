import re, numpy as np, pandas as pd
from common import *

FEATURES=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']

def link_disease(file_name):
    d=read_csv(f'06_ML_DATASETS/{file_name}')
    y=read_csv('07_MODELING/02_YIELD_BASELINE_CORRECTED/ML_YIELD_CORRECTED_MODEL_READY.csv')
    y['key']=y['canonical_genotype_candidate'].map(norm_name)
    yh=y.groupby('key')[FEATURES].median(numeric_only=True)
    d['key']=d['canonical_genotype_candidate'].map(norm_name)
    z=d.join(yh,on='key',rsuffix='_linked')
    for c in FEATURES:
        z[c]=pd.to_numeric(z.get(c+'_linked', np.nan),errors='coerce')
    z['link_confidence']=np.where(z[FEATURES].notna().all(axis=1),'EXACT_NAME_FULL_FEATURE_LINK',np.where(z[FEATURES].notna().sum(axis=1)>=4,'EXACT_NAME_PARTIAL_FEATURE_LINK','NO_USABLE_FEATURE_LINK'))
    return z


def regression_task(df,target,prefix,out):
    df=df[pd.to_numeric(df[target],errors='coerce').notna()].copy(); df[target]=pd.to_numeric(df[target],errors='coerce')
    df=df[df[FEATURES].notna().sum(axis=1)>=4].copy()
    if len(df)<25:
        log(f'{prefix} regression skipped: only {len(df)} usable rows')
        return
    df['genotype_id_candidate']=df['key']
    tr,va,te=grouped_train_val_test(df,'genotype_id_candidate')
    save_csv(df,out/f'{prefix}_REGRESSION_READY.csv')
    save_csv(tr,out/f'{prefix}_train.csv'); save_csv(va,out/f'{prefix}_validation.csv'); save_csv(te,out/f'{prefix}_test.csv')
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor,ExtraTreesRegressor,GradientBoostingRegressor,HistGradientBoostingRegressor
    models={
      'DummyMean':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',DummyRegressor())]),
      'Ridge':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',Ridge(alpha=10))]),
      'RandomForest':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',RandomForestRegressor(n_estimators=400,min_samples_leaf=2,random_state=SEED,n_jobs=-1))]),
      'ExtraTrees':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',ExtraTreesRegressor(n_estimators=400,min_samples_leaf=2,random_state=SEED,n_jobs=-1))]),
      'GradientBoosting':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',GradientBoostingRegressor(n_estimators=250,max_depth=2,learning_rate=.04,random_state=SEED))]),
      'HistGradientBoosting':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingRegressor(max_iter=250,learning_rate=.05,max_leaf_nodes=15,random_state=SEED))])}
    xb=try_xgb_regressor()
    if xb is not None: models['XGBoost']=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',xb)])
    rows=[]
    for name,m in models.items():
        log(f'Training {name} {prefix} regression model...')
        m.fit(numeric_feature_frame(tr,FEATURES),tr[target])
        pva=m.predict(numeric_feature_frame(va,FEATURES)); pte=m.predict(numeric_feature_frame(te,FEATURES))
        mv=regression_metrics(va[target],pva); mt=regression_metrics(te[target],pte)
        rows.append({'model':name,'validation_MAE':mv['MAE'],'validation_RMSE':mv['RMSE'],'validation_R2':mv['R2'],'test_MAE':mt['MAE'],'test_RMSE':mt['RMSE'],'test_R2':mt['R2']})
        pd.DataFrame({'entity_name':te.canonical_genotype_candidate,'target':te[target],'prediction':pte,'link_confidence':te.link_confidence}).to_csv(out/f'{prefix}_{name}_test_predictions.csv',index=False)
        import joblib; joblib.dump(m,out/f'{prefix}_{name}.joblib')
        log(f'{name} {prefix} regression model done')
    save_csv(pd.DataFrame(rows).sort_values('validation_RMSE'),out/f'{prefix}_REGRESSION_MODEL_COMPARISON.csv')


def classification_task(df,target,prefix,out):
    df=df[df[target].notna()].copy(); df=df[df[FEATURES].notna().sum(axis=1)>=4].copy()
    if len(df)<30 or df[target].nunique()<2:
        log(f'{prefix} classification skipped: insufficient usable data')
        return
    df['genotype_id_candidate']=df['key']
    tr,va,te=grouped_train_val_test(df,'genotype_id_candidate')
    # Drop validation/test unseen labels from metrics only; model can still train if train has them.
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier,ExtraTreesClassifier,HistGradientBoostingClassifier
    models={
      'LogisticRegression':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',LogisticRegression(max_iter=3000,class_weight='balanced'))]),
      'SVM':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('sc',StandardScaler()),('m',SVC(class_weight='balanced'))]),
      'RandomForest':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',RandomForestClassifier(n_estimators=400,min_samples_leaf=2,class_weight='balanced_subsample',random_state=SEED,n_jobs=-1))]),
      'ExtraTrees':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',ExtraTreesClassifier(n_estimators=400,min_samples_leaf=2,class_weight='balanced',random_state=SEED,n_jobs=-1))]),
      'HistGradientBoosting':Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',HistGradientBoostingClassifier(max_iter=250,learning_rate=.05,max_leaf_nodes=15,l2_regularization=1.0,random_state=SEED))])}
    rows=[]
    for name,m in models.items():
        log(f'Training {name} {prefix} classification model...')
        m.fit(numeric_feature_frame(tr,FEATURES),tr[target])
        for split,ds in [('validation',va),('test',te)]:
            pred=m.predict(numeric_feature_frame(ds,FEATURES))
            met=classification_metrics(ds[target],pred)
            rows.append({'model':name,'split':split,**{k:v for k,v in met.items()}})
        import joblib; joblib.dump(m,out/f'{prefix}_{name}_classifier.joblib')
        log(f'{name} {prefix} classification model done')
    save_csv(pd.DataFrame(rows),out/f'{prefix}_CLASSIFICATION_MODEL_COMPARISON.csv')


def main():
    log('STEP 3/9: TRAINING TLB AND SDM DISEASE MODELS')
    out=output_dir(3,'DISEASE_MODELS')
    for f,score,reaction,prefix in [
        ('ML_TLB_READY.csv','tlb_disease_score','tlb_reaction','TLB'),
        ('ML_SDM_READY.csv','sdm_pdi','sdm_reaction','SDM')]:
        log(f'Preparing {prefix} data and linking phenotype features by exact normalized genotype name...')
        z=link_disease(f)
        save_csv(z,out/f'{prefix}_LINK_AUDIT.csv')
        log(f'{prefix} full feature links: {int((z[FEATURES].notna().all(axis=1)).sum())} / {len(z)}')
        regression_task(z,score,prefix,out)
        classification_task(z,reaction,prefix,out)
    (out/'README.txt').write_text('Disease models use pathology targets from the disease trials and pre-harvest agronomic features linked by exact normalized genotype name to the corrected yield dataset. This is cross-trial exploratory modeling, not proof of causal disease resistance. Link audit is retained. Severe class imbalance is expected for SDM.\n',encoding='utf-8')
    log('DISEASE MODEL TRAINING DONE')

if __name__=='__main__': main()
