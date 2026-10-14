import json, shutil
from pathlib import Path
from common import *

def main():
    log('STEP 8/9: PACKAGING BEST AVAILABLE MODELS FOR REUSE')
    out=output_dir(8,'MODEL_PACKAGE')
    models_dir=pipeline_root()/'models'; models_dir.mkdir(exist_ok=True)
    candidates={
      'yield_tuned_random_forest':output_dir(6,'TUNING')/'YIELD_TUNED_RANDOM_FOREST.joblib',
      'tlb_tuned_extratrees':output_dir(6,'TUNING')/'TLB_TUNED_EXTRATREES.joblib',
      'sdm_tuned_extratrees':output_dir(6,'TUNING')/'SDM_TUNED_EXTRATREES.joblib',
      'tlb_tuned_random_forest_classifier':output_dir(6,'TUNING')/'TLB_TUNED_RANDOM_FOREST_CLASSIFIER.joblib',
      'sdm_tuned_random_forest_classifier':output_dir(6,'TUNING')/'SDM_TUNED_RANDOM_FOREST_CLASSIFIER.joblib',
    }
    manifest=[]
    for name,p in candidates.items():
        if p.exists():
            dest=models_dir/(name+'.joblib'); shutil.copy2(p,dest); manifest.append({'model':name,'path':str(dest.relative_to(project_root())),'status':'PACKAGED'})
            log(f'Packaged {name}')
        else:
            manifest.append({'model':name,'path':str(p),'status':'NOT_AVAILABLE'})
            log(f'No trained artifact for {name}; package entry retained')
    save_csv(__import__('pandas').DataFrame(manifest),out/'MODEL_PACKAGE_MANIFEST.csv')
    metadata={'project':'maize_ai_ml_digitalization','created_at':now(),'notes':'Models are research artifacts. Validate on independent seasons/locations before operational decisions.','feature_schema':{
      'yield':['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage'],
      'disease':['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']}}
    json_dump(metadata,out/'MODEL_METADATA.json')
    (out/'predict_example.py').write_text('''from pathlib import Path\nimport joblib, pandas as pd\nMODEL=Path(__file__).parents[2]/"models"/"yield_tuned_random_forest.joblib"\nFEATURES=["days_to_50_percent_pollen_shedding","days_to_50_percent_silking","days_to_75_percent_dry_husk","plant_height","ear_height","plant_stand","shelling_percentage"]\nmodel=joblib.load(MODEL)\nX=pd.DataFrame([{f:0.0 for f in FEATURES}])\nprint(model.predict(X))\n''',encoding='utf-8')
    log('MODEL PACKAGING DONE')

if __name__=='__main__': main()
