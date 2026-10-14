$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python -ErrorAction Stop
$env:PYTHONPATH = "$Root;$((Split-Path -Parent $Root))"
$env:LOKY_MAX_CPU_COUNT='4'
& $Python.Source (Join-Path $Root 'scripts\run_server.py')
