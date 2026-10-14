# Phase 10-12 contingency plan

Run normally from the project root:

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1
```

The menu uses:

```text
1 = Next phase
2 = Previous phase
3 = Redo current/failed phase
4 = Run all remaining
5 = Run selected phase
6 = Status
7 = Install requirements
8 = Exit
```

## Phase 10 review

Edit:

`10_12_NEXT_PHASES\outputs\PHASE_10_GENOTYPE_REVIEW\GENOTYPE_IDENTITY_DECISIONS.csv`

Use only:

- `CONFIRMED` when identity is confirmed
- `PENDING_REVIEW` while unresolved
- `EXCLUDED` when the row/group must not enter production modeling

Then rerun Phases 10-12.

## If packages are missing

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action install
```

## If a phase fails

Read the newest `10_12_NEXT_PHASES\logs\phase_*.log`, fix the issue, then:

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action redo
```

## If you want a specific phase

```powershell
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 10
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 11
.\10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1 -Action run -Stage 12
```

## Scientific contingency

Location/season holdouts are reported as unavailable when the actual project data contains only one group. Do not manufacture a holdout. Add genuinely independent data later and rerun Phase 12.

If some cross-validation folds have unavailable classification metrics because a fold has only one training class, the output records the usable folds rather than pretending the metric is available.
