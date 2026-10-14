# Contingency plan for Phases 16–18

## General rule
A Python warning is not a failure. A non-zero Python exit code is a failure. The PowerShell runner uses Start-Process + redirected stdout/stderr and checks `ExitCode` only.

## Phase 16

### No weather-disease linked data
Expected. Phase 16 writes a blocker/status report, a data requirements file, and a template, then exits successfully so Phases 17–18 can continue.

### Weather file exists but is malformed
The phase creates a clear input-error report and exits non-zero. Fix the CSV and use `-Action redo`.

### Too few time points
The phase reports `INSUFFICIENT_TIME_POINTS` and does not train a misleading model. It still exits successfully when the file is absent; if the user supplied an explicit linked file, malformed/insufficient data is a controlled non-zero error.

### XGBoost unavailable
Optional. The phase continues with scikit-learn models.

## Phase 17

### A selected model or dataset is missing
The phase skips that model, records the missing item, and continues. If every explainability target is missing, it creates a blocker report and exits successfully.

### Grouped CV has too few groups
The phase uses the maximum safe number of groups (minimum 2), otherwise skips the analysis with a recorded reason.

### Classification test fold contains one class
Handled explicitly with zero-division-safe metrics; no sklearn confusion-matrix warning is allowed to stop the stage.

## Phase 18

### Model package missing
Prediction returns an explicit `MODEL_UNAVAILABLE` status rather than fabricating a prediction.

### Input columns missing
The engine preserves the row and marks `input_completeness=PARTIAL_INPUT_MODEL_IMPUTED`; the model pipeline may impute numeric features. Missingness is never hidden.

### Model feature schema differs
The engine uses the feature list stored inside the model package. Unsupported features are reported in the output schema rather than guessed.

### Bad numeric value
The engine converts invalid numerics to NaN and reports the affected fields.

### Regression output outside the expected physical scale
The engine does not silently clip it. It returns the raw prediction plus a range flag.
