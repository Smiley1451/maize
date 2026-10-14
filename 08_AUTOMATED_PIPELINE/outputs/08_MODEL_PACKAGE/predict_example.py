from pathlib import Path
import joblib, pandas as pd
MODEL=Path(__file__).parents[2]/"models"/"yield_tuned_random_forest.joblib"
FEATURES=["days_to_50_percent_pollen_shedding","days_to_50_percent_silking","days_to_75_percent_dry_husk","plant_height","ear_height","plant_stand","shelling_percentage"]
model=joblib.load(MODEL)
X=pd.DataFrame([{f:0.0 for f in FEATURES}])
print(model.predict(X))
