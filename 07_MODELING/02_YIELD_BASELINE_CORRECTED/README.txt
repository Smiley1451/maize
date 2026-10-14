STAGE 07.2 — CORRECTED YIELD BASELINE MODELING
================================================

This stage supersedes the diagnostic yield run after a target-unit audit.

Critical correction
-------------------
The source PDFs contain both:
- yield tables reported in t/ha for coordinated NIVT/AVT/QPM trials
- yield tables reported in kg/ha for several station/private-company/grain-yield trials.

The earlier standardized trait mapping had incorrectly mapped some kg/ha variables
to the canonical grain_yield unit t/ha and the analysis-ready table therefore
mixed scales. This stage rebuilds the target directly from the raw source values:
`t/ha` values are multiplied by 1,000 and `kg/ha` values are kept unchanged.

Summary/statistical rows such as C.V, C.D, General Mean and Location Mean are
removed from the genotype-level prediction target.

Target
------
grain_yield_kg_ha_corrected

Feature sets
------------
EARLY:
days_to_50_percent_pollen_shedding
days_to_50_percent_silking
days_to_75_percent_dry_husk
plant_height
ear_height
plant_stand

EXTENDED:
EARLY + shelling_percentage

Models
------
Dummy mean, Linear Regression, Ridge, Random Forest, Extra Trees,
HistGradientBoosting, Gradient Boosting, XGBoost.

Selection
---------
Lowest validation RMSE, then MAE, then higher R2. Winner is refit on train +
validation and checked on a genotype-disjoint held-out test set.

Important
---------
This is still an exploratory baseline. Genotype identity/review flags remain and
the source data span heterogeneous experiments at ZARS, Mandya. Do not use this
for deployment or breeding recommendations without further validation.
