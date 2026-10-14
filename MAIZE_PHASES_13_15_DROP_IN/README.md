# MAIZE Phases 13-15 Drop-In

This folder continues the completed Phases 10-12 project.

## Phases

13. Advanced yield modeling + feature engineering
14. Advanced TLB/SDM disease modeling
15. Multi-trait genotype breeding intelligence (PCA, clustering, Pareto screening)

## Drop-in use

Extract this folder into the project root so that:

`<project-root>/13_15_NEXT_PHASES/`

From the project root run only:

`.[?1h.[?1l\13_15_NEXT_PHASES\RUN_PHASES_13_15.ps1`

The pipeline is interactive and supports next, previous, redo, run-all, selected stage, install, status, and verification.

The code uses Phase 10-12 outputs as upstream inputs and does not alter source-preserved data.

## Important data safeguard
Phase 13 re-audits the yield target from the source-preserved `value` and `unit` fields. This is intentional because derived downstream fields can contain unit-conversion mistakes; the Phase 13 audit reports any discrepancy instead of changing the source data.

## Phase 15 cross-domain join
The breeding-intelligence module found 106 exact normalized genotype-name matches across yield, TLB, and SDM in the validation environment. The run-time pipeline recomputes this from the current Phase 13/14 outputs; it does not hard-code the count.
