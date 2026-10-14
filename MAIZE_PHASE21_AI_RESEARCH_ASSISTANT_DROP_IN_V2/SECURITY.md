# Phase 21 security notes

- Project-root paths are used for retrieval; no arbitrary filesystem path requested by a chat question is opened directly.
- Model artifact detail is constrained to existing `.joblib` files under the project root.
- LLM calls send only selected evidence/tool results for the current query; the complete project directory is not uploaded automatically.
- API runs on loopback (`127.0.0.1`) by default.
- Do not place real API keys in source files. Use environment variables.
- Treat model artifacts as trusted local code/data because `joblib` deserialization can execute code when loading untrusted files.
