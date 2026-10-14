# Phase 21 architecture

```text
User question
   |
   v
Question router / planner
   |
   +--> semantic retrieval over indexed PDFs, CSVs, logs, code, JSON, MD, PS1, etc.
   |
   +--> structured CSV tools (exact genotype/experiment/record queries)
   |
   +--> model artifact + metrics + explainability tools
   |
   +--> Phase 19 health/metadata and local model prediction fallback
   |
   +--> project file/pipeline tools
   |
   v
Evidence set
   |
   +--> external OpenAI-compatible / Ollama synthesis when configured
   |
   +--> deterministic grounded local fallback otherwise
   |
   v
Answer + source locations + tools used
```

The assistant intentionally keeps binary `.joblib` files out of text retrieval. They are catalogued as artifacts and can be loaded only through model tools.
