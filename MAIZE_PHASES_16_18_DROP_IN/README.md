# MAIZE Phases 16–18 Drop-In Package

This folder is designed to be copied directly into the existing project root.

## Phases

16. Weather-driven disease forecasting readiness + optional time-aware model
17. Model explainability + error analysis
18. Reusable prediction engine for yield, TLB and SDM

## Windows start

From the main project root:

```powershell
$env:LOKY_MAX_CPU_COUNT="4"
.\MAIZE_PHASES_16_18_DROP_IN\RUN_PHASES_16_18.ps1
```

Press **4** to run all remaining phases.

The runner determines success from the Python process exit code. Python warnings written to stderr are displayed in yellow but do not terminate a successful stage.

## Optional weather data

Phase 16 completes in a controlled `WAITING_FOR_ALIGNED_DATA` state when no verified weather+disease linked file is available. It never invents disease labels. To run the optional forecasting path, place a CSV at:

`MAIZE_PHASES_16_18_DROP_IN/config/WEATHER_DISEASE_LINKED.csv`

Use `config/WEATHER_DISEASE_LINKED_TEMPLATE.csv` as the schema template.

## Prediction engine

After Phase 18, run:

```powershell
.\MAIZE_PHASES_16_18_DROP_IN\RUN_PREDICTION.ps1 -InputCsv ".\sample_prediction_input.csv"
```

The engine loads the Phase 13/14 selected model packages when available, with controlled fallback to the existing 08_AUTOMATED_PIPELINE package only when the input schema is compatible.

## Recovery

- `-Action next` – run next phase
- `-Action prev` – run previous phase again
- `-Action redo` – rerun current/failed phase
- `-Action retry` – alias for redo
- `-Action all` – run all remaining phases, stopping on the first real failure
- `-Action run -Stage 16|17|18` – run one phase
- `-Action status` – show state
- `-Action install` – install core requirements and optionally xgboost
- `-Action verify` – verify generated outputs and code

All phase state is stored in `phase_state.json` inside this drop-in folder.
