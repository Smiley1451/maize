# Optional LLM setup

The assistant is functional without any external model. To enable higher-quality natural-language synthesis, configure an OpenAI-compatible endpoint.

## OpenAI-compatible

```powershell
$env:MAIZE_LLM_PROVIDER="openai_compatible"
$env:MAIZE_LLM_BASE_URL="https://api.openai.com/v1"
$env:MAIZE_LLM_API_KEY="YOUR_KEY"
$env:MAIZE_LLM_MODEL="YOUR_MODEL"
```

## Local Ollama-compatible endpoint

```powershell
$env:MAIZE_LLM_PROVIDER="ollama"
$env:MAIZE_LLM_BASE_URL="http://127.0.0.1:11434/v1"
$env:MAIZE_LLM_API_KEY="ollama"
$env:MAIZE_LLM_MODEL="YOUR_LOCAL_MODEL"
```

The assistant still grounds the answer in project retrieval/tools; the LLM is used for synthesis, not as the source of project facts.
