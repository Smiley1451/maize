from __future__ import annotations
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_16_18 import *

from prediction_engine import predict_dataframe, find_model

OUT18=phase_out('18_PREDICTION_ENGINE')


def main():
    log('='*62); log('PHASE 18: REUSABLE PREDICTION ENGINE'); log('='*62)
    # Write an operational schema without requiring a prediction input yet.
    schema=[
        ('genotype','identifier'),('days_to_50_percent_pollen_shedding','numeric feature'),('days_to_50_percent_silking','numeric feature'),('days_to_75_percent_dry_husk','numeric feature'),('plant_height','numeric feature'),('ear_height','numeric feature'),('plant_stand','numeric feature'),('shelling_percentage','numeric feature')
    ]
    save(pd.DataFrame(schema,columns=['column','role']),OUT18/'PREDICTION_INPUT_SCHEMA.csv')
    model_rows=[]
    for key,names in {
        'yield':['yield_advanced_selected.joblib','yield_tuned_random_forest.joblib'],
        'tlb_regression':['tlb_advanced_regression_selected.joblib','tlb_tuned_extratrees.joblib'],
        'tlb_classifier':['tlb_advanced_classifier_selected.joblib','tlb_tuned_random_forest_classifier.joblib'],
        'sdm_regression':['sdm_advanced_regression_selected.joblib','sdm_tuned_extratrees.joblib'],
        'sdm_classifier':['sdm_advanced_classifier_selected.joblib','sdm_tuned_random_forest_classifier.joblib']}.items():
        p=find_model(*names); model_rows.append({'model_key':key,'resolved_path':str(p) if p else '','available':bool(p)})
    save(pd.DataFrame(model_rows),OUT18/'MODEL_AVAILABILITY.csv')
    (OUT18/'PREDICTION_ENGINE_USAGE.txt').write_text('Use RUN_PREDICTION.ps1 with a CSV input. The engine preserves missingness, uses the feature schema stored in model packages, and reports range flags without clipping predictions.\n',encoding='utf-8')
    # Generate sample input and output if at least one model is available.
    sample=ROOT/'sample_prediction_input.csv'
    if not sample.exists():
        sample.write_text('genotype,days_to_50_percent_pollen_shedding,days_to_50_percent_silking,days_to_75_percent_dry_husk,plant_height,ear_height,plant_stand,shelling_percentage\nSAMPLE-GENOTYPE,70,72,112,220,115,70000,82.0\n',encoding='utf-8')
    d=pd.read_csv(sample)
    out=predict_dataframe(d)
    out.to_csv(OUT18/'SAMPLE_PREDICTIONS.csv',index=False)
    log('PHASE 18 DONE: prediction engine schema and model runtime registry created.')

if __name__=='__main__': main()
