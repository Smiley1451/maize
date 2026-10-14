# Contingency Plan — Phases 13-15

1. If a phase fails, use `-Action redo` or run it explicitly with `-Action run -Stage <13|14|15>`.
2. If XGBoost is unavailable, the pipeline automatically skips XGBoost and continues with sklearn models.
3. If a dataset is missing, the phase stops with a precise input-path message; do not create replacement data by hand.
4. Phase 13 re-audits yield units from the original `unit` + `value` columns. This protects against stale derived values in Phase 11.
5. Phase 14 reports class imbalance and may mark classification as LOW_SUPPORT/SEVERE_IMBALANCE without pretending that accuracy proves generalization.
6. Phase 15 uses exact normalized genotype names for cross-domain joins and preserves a match-method field.
7. If fewer than 2 valid PCA/clustering rows remain, Phase 15 will stop rather than fabricate clusters.
8. All model selection is based on cross-validation metrics. No model is called production-grade until independent external validation is available.
