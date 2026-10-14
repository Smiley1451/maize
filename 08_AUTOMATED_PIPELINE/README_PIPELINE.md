# Automated Maize AI/ML Pipeline

This is the reproducible training and project-completion layer added to the consolidated maize digitization project.

## Windows PowerShell — recommended

Open PowerShell in the project root (the folder that contains `08_AUTOMATED_PIPELINE`) and run:

```powershell
cd .\08_AUTOMATED_PIPELINE
.\run_pipeline.ps1
```

The controller is interactive.

```text
1 = Next step
2 = Previous step
3 = Redo current/failed step
4 = Run all remaining
5 = Run a selected step
6 = Retry failed step
7 = Status
8 = Exit
```

You can also run commands directly:

```powershell
.\run_pipeline.ps1 -Action next
.\run_pipeline.ps1 -Action prev
.\run_pipeline.ps1 -Action redo
.\run_pipeline.ps1 -Action all
.\run_pipeline.ps1 -Action run -Stage 3
.\run_pipeline.ps1 -Action retry
.\run_pipeline.ps1 -Action status
```

To avoid automatic dependency installation:

```powershell
.\run_pipeline.ps1 -NoInstall
```

## Python 3.13

Use **PowerShell**, not the Python `>>>` prompt, to start the project script. The Python prompt is only for interactive Python commands.

Example:

```text
PS C:\Users\smile> cd C:\path\to\MAIZE_AI_ML_DIGITALIZATION_PROJECT
PS C:\path\to\MAIZE_AI_ML_DIGITALIZATION_PROJECT> .\08_AUTOMATED_PIPELINE\run_pipeline.ps1
```

## Stages

1. **Readiness audit** — verifies required input files and target units.
2. **Yield baseline** — rebuilds grain-yield target from source observations, converts t/ha to kg/ha, removes statistical summary rows, and trains multiple regression models.
3. **Disease models** — links pathology outcomes to agronomic traits using exact normalized genotype names, then trains TLB and SDM regression/classification models when enough usable features exist.
4. **PCA + clustering** — explores genotype structure with PCA, K-Means and agglomerative clustering.
5. **Weather risk readiness** — prepares weather features and explicitly blocks predictive disease-risk training until verified date/location disease outcomes are available.
6. **Tuning** — uses group-aware cross-validation to tune models without genotype leakage.
7. **Explainability** — generates permutation-importance outputs for available tuned models.
8. **Packaging** — copies reusable model artifacts and writes model metadata and an example prediction script.
9. **Final verification** — checks project folders, CSV readability, Python syntax, expected artifacts and final status.

## Contingency rules

- Missing core Python packages: the PowerShell launcher attempts `pip install -r requirements.txt`. Use `-NoInstall` to disable this.
- XGBoost unavailable: the modeling scripts continue with scikit-learn models.
- Too few usable disease-linked rows/features: that disease subtask is recorded as skipped instead of fabricating data.
- Severe SDM class imbalance: metrics include macro-F1 and balanced accuracy; no class balancing is hidden.
- Weather labels not aligned to disease observations: weather model is explicitly deferred and a blocker file is created.
- A stage fails: state is saved, logs are retained, and the menu supports retry/redo or moving back.
- Ctrl+C: previously completed outputs remain on disk; rerun the failed/current step.
- Do not edit files under source/previous stages during model development unless a new versioned modeling branch is created.

## Important scientific safeguards

The pipeline uses genotype-grouped splits to reduce train/test leakage. Target-specific preprocessing is performed inside scikit-learn pipelines. Disease phenotype linkage is retained as an audit. Cross-trial disease models are exploratory until independently validated. No weather-driven disease model is trained from unverified labels.

## Output locations

All new run products are written under:

`08_AUTOMATED_PIPELINE/outputs/`

Logs are under:

`08_AUTOMATED_PIPELINE/logs/`

Reusable packaged models are under:

`08_AUTOMATED_PIPELINE/models/`

The controller saves its progress in:

`08_AUTOMATED_PIPELINE/pipeline_state.json`
