# Phase 21 contingency plan

1. **No index** → run `-Action index` or choose menu option 1. Chat auto-builds the index on first use.
2. **Some PDFs fail extraction** → assistant still uses digitized `*_source_text_by_page.csv` files and other text artifacts; errors are recorded in the index manifest.
3. **CSV is malformed** → file is skipped by structured tools but remains in the file registry; retrieval errors are logged.
4. **Phase 19 API is offline** → model metadata and project artifacts remain searchable; prediction requests report backend unavailable instead of fabricating predictions.
5. **No LLM key** → deterministic grounded local fallback works; set `MAIZE_LLM_PROVIDER` later for LLM synthesis.
6. **LLM provider fails/timeouts** → automatically fall back to grounded local answer mode.
7. **New project files added** → run `-Action index` to refresh; the old index remains until the new build finishes.
8. **Test failure** → run `-Action test`, inspect `outputs/PYTEST_OUTPUT.txt`, fix the failing component, then rerun.
9. **Port 8010 is busy** → set `$env:MAIZE_ASSISTANT_PORT='8011'` and restart.
10. **Windows stderr warning** → the PowerShell runner uses process exit code and does not treat ordinary Python stderr text as automatic failure.
