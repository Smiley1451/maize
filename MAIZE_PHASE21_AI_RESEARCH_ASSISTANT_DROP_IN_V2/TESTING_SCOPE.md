# Testing scope

The Phase 21 suite covers parser behavior, index construction, semantic retrieval, structured CSV tools, genotype lookup, assistant routing, deterministic grounded chat, FastAPI health/status/tools/models/search/chat/source endpoints, model inventory, project-root safety, and full project indexing.

The benchmark additionally runs 15 representative project questions. With no LLM configured, evaluation checks that a grounded response and project evidence are produced. For production-quality semantic evaluation with an external LLM, review the generated answers and citations and optionally expand `config/benchmark_questions.json` with gold answers.
