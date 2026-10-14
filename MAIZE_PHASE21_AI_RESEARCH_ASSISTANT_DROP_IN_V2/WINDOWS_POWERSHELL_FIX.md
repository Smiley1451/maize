# Windows PowerShell compatibility note

The Phase 21 runner is ASCII-only so it can be parsed correctly by Windows PowerShell 5.1 as well as PowerShell 7+.

Do not change the ASCII punctuation in RUN_PHASE21.ps1 to smart quotes or long dash characters.

Recommended commands from the project root:

```powershell
$env:LOKY_MAX_CPU_COUNT="4"
.\MAIZE_PHASE21_AI_RESEARCH_ASSISTANT_DROP_IN\RUN_PHASE21.ps1 -Action verify
```

The runner determines success from the Python process exit code. Python warnings written to stderr are logged but do not by themselves mark the step as failed.
