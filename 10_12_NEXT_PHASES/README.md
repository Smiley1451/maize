# Phases 10-12: Genotype Review -> Production Datasets -> Generalization Validation

Paste this folder directly into the root of `MAIZE_AI_ML_DIGITALIZATION_PROJECT`.

## Single Windows command

From the project root:

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1
```

This opens a small menu. The pipeline state is stored in `phase_state.json` so completed phases are not accidentally repeated.

### Menu

```text
1 = Next phase
2 = Previous phase
3 = Redo current/failed phase
4 = Run all remaining phases
5 = Run selected phase
6 = Status
7 = Install requirements
8 = Verify phases 10-12
9 = Exit
```

You can also use direct commands:

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action all
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action next
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action prev
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action redo
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action status
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 10
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 11
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 12
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action install
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action verify
```

## Phase 10 - Genotype identity review

Builds a controlled identity decision table from the existing genotype master and analysis master. Unique source names can be auto-confirmed. Alias groups remain visible for review. Domain-safe identity is recorded so one domain can proceed without silently treating all cross-domain category differences as the same biological identity.

Edit:

`outputs\PHASE_10_GENOTYPE_REVIEW\GENOTYPE_IDENTITY_DECISIONS.csv`

Allowed values in `final_status`:

- `CONFIRMED`
- `PENDING_REVIEW`
- `EXCLUDED`

Phase 10 also creates both `GENOTYPE_IDENTITY_MASTER.csv` and `GENOTYPE_IDENTITY_DOMAIN_MASTER.csv`.

## Phase 11 - Production datasets

Rebuilds strict modeling datasets from Phase 10 identity rules instead of modifying the source-preserved data.

Outputs:

- `YIELD_PRODUCTION_STRICT.csv`
- `TLB_PRODUCTION_STRICT.csv`
- `SDM_PRODUCTION_STRICT.csv`
- exploratory all-identity files
- multi-trait production summary
- dataset manifest and rules

Yield is converted to kg/ha only when the recorded unit is t/ha or kg/ha. Unknown yield units remain unavailable.

## Phase 12 - Generalization validation

Runs grouped genotype cross-validation and leave-one-experiment-out validation where enough independent experiments exist. It also reports whether real location and season holdouts are available.

No synthetic future/location data is created. Lack of an independent location or season is reported explicitly.

## Recovery

Every phase writes a timestamped log under `logs\`.

If a phase fails:

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action redo
```

or rerun a specific phase:

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 12
```

To start from a clean checkpoint, delete only `phase_state.json`; do not delete the source data.
