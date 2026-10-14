MAIZE ML DATASET STAGE

Created target-specific starter datasets from the analysis master.

Yield:
- ML_YIELD_READY.csv: 191 target-bearing genotype x experiment rows.
- Features are only pre-harvest agronomic variables. Grain yield is target.

TLB:
- ML_TLB_READY.csv and ML_TLB_CLASSIFICATION_READY.csv use disease observations linked to median phenotype features from yield trials for the same candidate genotype.

SDM:
- ML_SDM_READY.csv and ML_SDM_CLASSIFICATION_READY.csv use the same phenotype linkage approach. NG is excluded from SDM classification targets.

Multi-trait:
- ML_MULTI_TRAIT_EXPLORATORY.csv is a genotype-level summary using medians across available trials. It is exploratory and should not be treated as a single-environment prediction dataset.

SPLITS:
- 70/15/15 approximate train/validation/test.
- Group-aware by candidate genotype_id to reduce genotype leakage.
- Split assignment is deterministic.

IMPORTANT:
- Values are not imputed in these CSVs. Imputation/scaling/encoding must be fit only on training data inside a pipeline.
- genotype_id_candidate is a grouping/audit field, not a model feature.
- Review flags are retained. For final scientific training, unresolved identity/source conflicts should be reviewed before release.
- TLB/SDM phenotype linkage is a useful exploratory baseline, not proof of causal relationships.
- Weather has not been merged because verified experiment-day linkage is not yet established.
