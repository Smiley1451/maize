# Phase 21 — Maize AI/LLM Research Assistant

This is a drop-in Phase 21 assistant for the existing MAIZE_AI_ML_DIGITALIZATION_PROJECT.
It treats the project folder as the source of truth and combines:
- recursive file discovery and registry
- PDF/TXT/MD/LOG/code/JSON/YAML/CSV ingestion
- lexical/semantic retrieval using local TF-IDF (no external vector DB required)
- exact/structured CSV querying
- genotype, experiment, model, cluster, weather, pipeline and project tools
- direct integration with the existing Phase 19 FastAPI backend when available
- optional OpenAI-compatible / Ollama LLM synthesis
- grounded citations to project file paths and row/page metadata
- deterministic local fallback when no LLM key/server is configured
- FastAPI chat/search endpoints
- CLI chat
- automated tests and evaluation

## Install and run

From the project root:

```powershell
$env:LOKY_MAX_CPU_COUNT="4"
.\21_AI_ASSISTANT\RUN_PHASE21.ps1
```

Press `4` to run full verification, or `1` to build/refresh the project index, `2` to start the chat, and `3` to run tests.

Direct commands:

```powershell
.\21_AI_ASSISTANT\RUN_PHASE21.ps1 -Action index
.\21_AI_ASSISTANT\RUN_PHASE21.ps1 -Action chat
.\21_AI_ASSISTANT\RUN_PHASE21.ps1 -Action test
.\21_AI_ASSISTANT\RUN_PHASE21.ps1 -Action eval
.\21_AI_ASSISTANT\RUN_PHASE21.ps1 -Action verify
```

## Optional LLM

The system works without an external LLM by using grounded local retrieval and structured tools. For LLM-level synthesis, set:

```powershell
$env:MAIZE_LLM_PROVIDER="openai_compatible"
$env:MAIZE_LLM_BASE_URL="https://api.openai.com/v1"
$env:MAIZE_LLM_API_KEY="YOUR_KEY"
$env:MAIZE_LLM_MODEL="YOUR_MODEL"
```

For a local Ollama server:

```powershell
$env:MAIZE_LLM_PROVIDER="ollama"
$env:MAIZE_LLM_BASE_URL="http://127.0.0.1:11434/v1"
$env:MAIZE_LLM_MODEL="YOUR_LOCAL_MODEL"
```

The assistant never requires an LLM to answer source-grounded questions.

## Design

`LLM -> planner/router -> project retrieval + structured data tools + model/API tools -> evidence -> answer`

Binary model files are catalogued as artifacts; they are not embedded as text. Model predictions are obtained via Phase 19 when reachable or by the local model loader as a fallback.

## Important behavior

- Recorded project facts are distinguished from derived calculations and ML predictions.
- Missing information is reported rather than invented.
- Source paths, CSV row context, or PDF page context are attached to evidence.
- The project is re-indexable after new phases or data are added.
