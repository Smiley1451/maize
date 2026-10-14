STAGE 07.0 — MODEL READINESS AUDIT

Key finding
-----------
The first yield modeling attempt revealed that the current model-ready target was
not on one consistent scale. The source data contain t/ha and kg/ha yield formats,
and some summary statistics had also been carried into the genotype-level table.

Resolution
----------
The corrected yield dataset is rebuilt from the raw master observations with an
explicit source-variable conversion rule and with summary rows removed.
See ../02_YIELD_BASELINE_CORRECTED/YIELD_UNIT_CORRECTION_AUDIT.csv and
ML_YIELD_CORRECTED_MODEL_READY.csv.
