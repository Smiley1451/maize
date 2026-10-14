STAGE 07.1 — YIELD REGRESSION BASELINE
=========================================

Purpose
-------
First-pass predictive modeling of `grain_yield` using the current ML yield dataset.

Feature sets
------------
1) early_traits
   days_to_50_percent_pollen_shedding
   days_to_50_percent_silking
   days_to_75_percent_dry_husk
   plant_height
   ear_height
   plant_stand

2) extended_traits_with_shelling
   all six early traits + shelling_percentage

The early-trait set is the primary intended forecasting use case. The extended
set is retained as a comparison because shelling_percentage may be strongly
predictive but is not as early in the crop workflow.

Models compared
---------------
Dummy mean, Linear Regression, Ridge, Random Forest, Extra Trees,
HistGradientBoosting, Gradient Boosting, XGBoost.

Training protocol
-----------------
- Existing train/validation/test splits are preserved.
- Genotype-group separation is audited.
- Median imputation is fit inside each training pipeline only.
- Linear models use training-fitted standardization.
- Model selection uses validation RMSE (then MAE, then higher R2).
- Selected winner is refit on train + validation.
- Test is held out for the final winner check.

Data-quality note
-----------------
Current ML rows contain PASS and REVIEW flags. This is an exploratory baseline.
Do not treat it as deployment-ready or publication-ready until identity and review
queues are resolved.

Next stages
-----------
07.2 Disease modeling: verify phenotype-to-pathology linkage, then TLB and SDM
regression/classification.
07.3 PCA + genotype clustering using multi-trait data.
07.4 Weather-driven disease risk modeling, conditional on experiment-date/weather
alignment.
07.5 Explainability and error analysis.
07.6 Hyperparameter tuning + grouped cross-validation.
07.7 Packaging/API/dashboard/final documentation.
