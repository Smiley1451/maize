import pandas as pd, numpy as np
from common import *

def explain_model(model_path, data_path, target, features, out_path, label, kind='regression'):
    import joblib
    if not model_path.exists() or not data_path.exists():
        return False
    d=pd.read_csv(data_path).dropna(subset=[target]).copy()
    d=d[d[features].notna().sum(axis=1)>=2]
    if len(d)<15:return False
    m=joblib.load(model_path)
    from sklearn.inspection import permutation_importance
    X=numeric_feature_frame(d,features); y=d[target]
    score='neg_root_mean_squared_error' if kind=='regression' else 'balanced_accuracy'
    r=permutation_importance(m,X,y,n_repeats=15,random_state=SEED,n_jobs=-1,scoring=score)
    imp=pd.DataFrame({'feature':features,'importance_mean':r.importances_mean,'importance_std':r.importances_std}).sort_values('importance_mean',ascending=False)
    save_csv(imp,out_path)
    return True

def main():
    log('STEP 7/9: RUNNING MODEL EXPLAINABILITY / FEATURE IMPORTANCE')
    out=output_dir(7,'EXPLAINABILITY')
    feats=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
    base=output_dir(2,'YIELD_BASELINE'); tuned=output_dir(6,'TUNING')
    model=tuned/'YIELD_TUNED_RANDOM_FOREST.joblib'
    data=base/'ML_YIELD_PIPELINE_READY.csv'
    if explain_model(model,data,'yield_kg_ha',feats,out/'YIELD_PERMUTATION_IMPORTANCE.csv','yield'):
        log('Yield explainability done')
    else:
        log('Yield explainability skipped: tuned model or data unavailable')
    for prefix,target in [('TLB','tlb_disease_score'),('SDM','sdm_pdi')]:
        model=tuned/f'{prefix}_TUNED_EXTRATREES.joblib'; data=output_dir(3,'DISEASE_MODELS')/f'{prefix}_REGRESSION_READY.csv'
        if explain_model(model,data,target,feats,out/f'{prefix}_PERMUTATION_IMPORTANCE.csv',prefix,'regression'): log(f'{prefix} regression explainability done')
        cmodel=tuned/f'{prefix}_TUNED_RANDOM_FOREST_CLASSIFIER.joblib'
        ctarget='tlb_reaction' if prefix=='TLB' else 'sdm_reaction'
        if explain_model(cmodel,data,ctarget,feats,out/f'{prefix}_CLASSIFIER_PERMUTATION_IMPORTANCE.csv',prefix,'classification'): log(f'{prefix} classification explainability done')
    (out/'INTERPRETATION_GUIDE.txt').write_text('Permutation importance is associative. Positive importance means shuffling the feature worsened model performance under the scoring setup; it is not a causal effect estimate. Use grouped validation/tuning outputs alongside this file.\n',encoding='utf-8')
    log('EXPLAINABILITY DONE')

if __name__=='__main__': main()
