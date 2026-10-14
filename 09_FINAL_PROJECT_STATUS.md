# Final Project Status — 2026-09-29

## Completed

The project now contains the complete digitization/validation/normalization/analysis/ML-data work plus an executable model-training pipeline.

### Automated pipeline stages

1. Model readiness audit
2. Yield baseline regression
3. TLB + SDM disease regression/classification
4. PCA + genotype clustering
5. Weather-risk data readiness
6. Group-aware hyperparameter tuning
7. Permutation-based explainability
8. Model packaging
9. Final project verification

## Model families implemented

### Yield
- Dummy mean baseline
- Ridge regression
- Random Forest regression
- Extra Trees regression
- Gradient Boosting regression
- HistGradientBoosting regression
- XGBoost regression when installed
- Group-aware Random Forest tuning

### TLB / SDM
- Disease-score regression
- Logistic Regression classification
- SVM classification
- Random Forest classification
- Extra Trees classification
- HistGradientBoosting classification
- XGBoost disease-score regression when installed
- Group-aware Extra Trees regression tuning
- Group-aware Random Forest classification tuning

### Unsupervised
- Standardization + median imputation
- PCA
- K-Means
- Agglomerative clustering
- Silhouette analysis
- Cluster trait profiles

### Weather
- Monthly weather feature preparation
- Weather summary features
- Explicit blocker when aligned disease labels are absent
- Optional time-aware weather/disease regression when `config/WEATHER_DISEASE_LINKED.csv` is supplied

## Reproducibility / leakage safeguards

- Grouped train/validation/test split by normalized genotype identity for baseline supervised tasks.
- Group-aware cross-validation for tuning.
- Missing-value handling stays inside model pipelines.
- Yield target conversion is performed in a new modeling dataset rather than modifying source-preserved values.
- Disease phenotype linkage uses an exact normalized genotype-name audit and is retained as an explicit cross-trial exploratory linkage.
- Weather modeling is not fabricated from unavailable target labels.

## Current generated run artifacts

The pipeline has been executed successfully through the final verification stage in the build environment. Generated artifacts are under `08_AUTOMATED_PIPELINE/outputs/` and reusable models are under `08_AUTOMATED_PIPELINE/models/`.

Final verification status: READY.

## Remaining scientific work

The remaining work is not a missing code problem; it is mainly additional data and validation:

1. Add more seasons/locations/replications to improve generalization.
2. Manually confirm genotype alias groups marked for review.
3. Obtain date/location-aligned TLB/SDM observations for weather-risk modeling.
4. Validate final models on an independent season/location that was not used for training or tuning.
5. Add dashboard/API only after model validation criteria are agreed.

## Windows start

From the extracted project folder:

```powershell
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1
```

For a specific stage:

```powershell
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action run -Stage 3
```

For the next step:

```powershell
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action next
```

For previous/redo/retry/all/status:

```powershell
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action prev
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action redo
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action retry
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action all
.\08_AUTOMATED_PIPELINE\run_pipeline.ps1 -Action status
```
