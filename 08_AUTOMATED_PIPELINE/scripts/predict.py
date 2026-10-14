from __future__ import annotations
import argparse
from pathlib import Path
import joblib, pandas as pd

ROOT=Path(__file__).resolve().parents[1]
FEATURES=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
MODELS={
 'yield':ROOT/'models/yield_tuned_random_forest.joblib',
 'tlb_score':ROOT/'models/tlb_tuned_extratrees.joblib',
 'sdm_pdi':ROOT/'models/sdm_tuned_extratrees.joblib',
 'tlb_class':ROOT/'models/tlb_tuned_random_forest_classifier.joblib',
 'sdm_class':ROOT/'models/sdm_tuned_random_forest_classifier.joblib',
}

def main():
 p=argparse.ArgumentParser(description='Run a packaged maize model on a CSV containing the required feature columns.')
 p.add_argument('--model',choices=MODELS,required=True)
 p.add_argument('--input',required=True,help='CSV containing the model feature columns')
 p.add_argument('--output',default='',help='Optional output CSV path')
 args=p.parse_args()
 model_path=MODELS[args.model]
 if not model_path.exists(): raise SystemExit(f'Model not found: {model_path}. Run pipeline steps 6-8 first.')
 df=pd.read_csv(args.input)
 missing=[c for c in FEATURES if c not in df.columns]
 if missing: raise SystemExit('Missing feature columns: '+', '.join(missing))
 model=joblib.load(model_path)
 pred=model.predict(df[FEATURES])
 out=df.copy(); out['prediction']=pred
 target=args.output or str(Path(args.input).with_name(Path(args.input).stem+'_'+args.model+'_prediction.csv'))
 out.to_csv(target,index=False)
 print(f'PREDICTION DONE: {args.model} model -> {target}')

if __name__=='__main__': main()
