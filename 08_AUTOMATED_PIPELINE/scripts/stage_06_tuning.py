import pandas as pd, numpy as np
from common import *

def tune_yield(out):
    ready=output_dir(2,'YIELD_BASELINE')/'ML_YIELD_PIPELINE_READY.csv'
    if not ready.exists():
        log('Yield baseline artifacts missing; tuning skipped')
        return
    d=pd.read_csv(ready); d['genotype_id_candidate']=d['genotype_key']
    from sklearn.model_selection import GroupKFold, RandomizedSearchCV
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor
    X=numeric_feature_frame(d,['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage'])
    y=d.yield_kg_ha
    pipe=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('model',RandomForestRegressor(random_state=SEED,n_jobs=1))])
    params={'model__n_estimators':[150,250,350],'model__max_depth':[None,3,5,8,12],'model__min_samples_leaf':[1,2,4,6],'model__max_features':[0.6,0.8,1.0]}
    cv=GroupKFold(n_splits=4)
    log('Tuning RandomForest yield model with GroupKFold...')
    rs=RandomizedSearchCV(pipe,params,n_iter=5,scoring='neg_root_mean_squared_error',cv=cv,n_jobs=1,random_state=SEED,refit=True,verbose=0)
    rs.fit(X,y,groups=d.genotype_id_candidate)
    import joblib; joblib.dump(rs.best_estimator_,out/'YIELD_TUNED_RANDOM_FOREST.joblib')
    pd.DataFrame([{'model':'RandomForest','best_cv_RMSE':-rs.best_score_,'best_params':str(rs.best_params_)}]).to_csv(out/'TUNING_RESULTS.csv',index=False)
    log('RandomForest yield tuning done')

def tune_disease(out):
    disease_out=output_dir(3,'DISEASE_MODELS')
    rows=[]
    for prefix,target in [('TLB','tlb_disease_score'),('SDM','sdm_pdi')]:
        p=disease_out/f'{prefix}_REGRESSION_READY.csv'
        if not p.exists(): continue
        d=pd.read_csv(p); d=d[d[target].notna()].copy();
        if len(d)<30: continue
        d['group']=d['key']; features=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
        X=numeric_feature_frame(d,features); y=d[target]
        from sklearn.model_selection import GroupKFold,RandomizedSearchCV
        from sklearn.pipeline import Pipeline
        from sklearn.impute import SimpleImputer
        from sklearn.ensemble import ExtraTreesRegressor
        pipe=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('model',ExtraTreesRegressor(random_state=SEED,n_jobs=1))])
        params={'model__n_estimators':[150,250,350],'model__max_depth':[None,3,5,8,12],'model__min_samples_leaf':[1,2,4]}
        cv=GroupKFold(n_splits=min(3,d.group.nunique()))
        log(f'Tuning ExtraTrees {prefix} disease regression...')
        rs=RandomizedSearchCV(pipe,params,n_iter=4,scoring='neg_root_mean_squared_error',cv=cv,n_jobs=1,random_state=SEED)
        rs.fit(X,y,groups=d.group)
        import joblib; joblib.dump(rs.best_estimator_,out/f'{prefix}_TUNED_EXTRATREES.joblib')
        rows.append({'target':target,'model':'ExtraTrees','best_cv_RMSE':-rs.best_score_,'best_params':str(rs.best_params_)})
        log(f'{prefix} disease tuning done')
    if rows: save_csv(pd.DataFrame(rows),out/'DISEASE_TUNING_RESULTS.csv')

def tune_disease_classifiers(out):
    disease_out=output_dir(3,'DISEASE_MODELS')
    rows=[]
    from sklearn.model_selection import GroupKFold, RandomizedSearchCV
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.ensemble import RandomForestClassifier
    for prefix,target in [('TLB','tlb_reaction'),('SDM','sdm_reaction')]:
        p=disease_out/f'{prefix}_REGRESSION_READY.csv'
        if not p.exists(): continue
        d=pd.read_csv(p)
        if target not in d.columns: continue
        d=d[d[target].notna()].copy()
        d['group']=d['key']
        features=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
        if len(d)<30 or d[target].nunique()<2: continue
        X=numeric_feature_frame(d,features); y=d[target]
        pipe=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('model',RandomForestClassifier(random_state=SEED,n_jobs=1))])
        params={'model__n_estimators':[150,250,350],'model__max_depth':[None,3,5,8,12],'model__min_samples_leaf':[1,2,4],'model__class_weight':['balanced','balanced_subsample',None]}
        cv=GroupKFold(n_splits=min(3,d.group.nunique()))
        log(f'Tuning RandomForest {prefix} disease classification...')
        rs=RandomizedSearchCV(pipe,params,n_iter=4,scoring='balanced_accuracy',cv=cv,n_jobs=1,random_state=SEED,refit=True)
        rs.fit(X,y,groups=d.group)
        import joblib; joblib.dump(rs.best_estimator_,out/f'{prefix}_TUNED_RANDOM_FOREST_CLASSIFIER.joblib')
        rows.append({'target':target,'model':'RandomForestClassifier','best_cv_balanced_accuracy':rs.best_score_,'best_params':str(rs.best_params_)})
        log(f'{prefix} disease classification tuning done')
    if rows: save_csv(pd.DataFrame(rows),out/'DISEASE_CLASSIFICATION_TUNING_RESULTS.csv')

def main():
    log('STEP 6/9: TUNING MODELS WITH GROUP-AWARE CROSS-VALIDATION')
    out=output_dir(6,'TUNING')
    tune_yield(out); tune_disease(out); tune_disease_classifiers(out)
    log('MODEL TUNING DONE')

if __name__=='__main__': main()
