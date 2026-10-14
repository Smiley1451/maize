[CmdletBinding()]
param(
    [ValidateSet('menu','start','start-bg','test','smoke','verify','install','status','openapi','docs')]
    [string]$Action = 'menu',
    [string]$ApiHost = '127.0.0.1',
    [int]$Port = 8000
)
$ErrorActionPreference = 'Stop'
$Base = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $Base
$env:MAIZE_PROJECT_ROOT = $ProjectRoot
$env:LOKY_MAX_CPU_COUNT = if ($env:LOKY_MAX_CPU_COUNT) { $env:LOKY_MAX_CPU_COUNT } else { '4' }
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw 'Python was not found on PATH. Install Python 3.13 and reopen PowerShell.' }

function Ensure-Imports {
    & $Python.Source -c "import fastapi,uvicorn,pydantic,pandas,numpy,joblib,sklearn; print('FASTAPI DEPENDENCIES OK')" 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'FASTAPI DEPENDENCIES MISSING. Installing...' -ForegroundColor Yellow
        & powershell -ExecutionPolicy Bypass -File (Join-Path $Base 'INSTALL_REQUIREMENTS.ps1')
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    }
}

function Run-PythonScript([string]$script, [string[]]$scriptArgs = @()) {
    & $Python.Source -u $script @scriptArgs 2>&1 | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) { throw "Python script failed: $script (exit code $LASTEXITCODE)" }
}

function Show-Status {
    Write-Host ''
    Write-Host 'PHASE 19 FASTAPI STATUS' -ForegroundColor Cyan
    Write-Host "Project root: $ProjectRoot"
    Write-Host "API target : http://$ApiHost`:$Port"
    try {
        $r = Invoke-RestMethod -Uri "http://$ApiHost`:$Port/api/v1/status" -Method Get -TimeoutSec 3
        Write-Host "API: $($r.api) | Models: $($r.models_available)/$($r.models_total)" -ForegroundColor Green
    } catch {
        Write-Host 'API: NOT RUNNING' -ForegroundColor Yellow
    }
}

switch ($Action) {
    'install' { & powershell -ExecutionPolicy Bypass -File (Join-Path $Base 'INSTALL_REQUIREMENTS.ps1') -UpgradePip; exit $LASTEXITCODE }
    'test' { Ensure-Imports; Run-PythonScript (Join-Path $Base 'scripts/run_full_tests.py'); exit 0 }
    'smoke' { Ensure-Imports; Run-PythonScript (Join-Path $Base 'scripts/smoke_test.py'); exit 0 }
    'verify' { Ensure-Imports; Run-PythonScript (Join-Path $Base 'scripts/verify_phase19.py'); exit 0 }
    'openapi' { Ensure-Imports; Run-PythonScript (Join-Path $Base 'scripts/export_openapi.py'); exit 0 }
    'status' { Show-Status; exit 0 }
    'docs' { Start-Process "http://$ApiHost`:$Port/docs"; exit 0 }
    'start-bg' {
        Ensure-Imports
        $logs = Join-Path $Base 'logs'; New-Item -ItemType Directory -Force -Path $logs | Out-Null
        $stdout = Join-Path $logs 'server.stdout.log'; $stderr = Join-Path $logs 'server.stderr.log'
        $args = "-u -m uvicorn app.main:app --host $ApiHost --port $Port"
        $p = Start-Process -FilePath $Python.Source -ArgumentList $args -WorkingDirectory $Base -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        Start-Sleep -Seconds 2
        Write-Host "FASTAPI BACKEND STARTED: PID=$($p.Id)" -ForegroundColor Green
        Write-Host "DOCS: http://$ApiHost`:$Port/docs" -ForegroundColor Cyan
        exit 0
    }
    'start' {
        Ensure-Imports
        & (Join-Path $Base 'START_FASTAPI.ps1') -ApiHost $ApiHost -Port $Port
        exit $LASTEXITCODE
    }
}

while ($true) {
    Write-Host ''
    Write-Host '==============================================================' -ForegroundColor DarkCyan
    Write-Host 'PHASE 19 - FASTAPI BACKEND' -ForegroundColor Cyan
    Write-Host '=============================================================='
    Write-Host '1 = Start API (foreground)'
    Write-Host '2 = Start API in background'
    Write-Host '3 = Run COMPLETE API test suite (all endpoints + cases)'
    Write-Host '10 = Run quick smoke test'
    Write-Host '4 = Verify Phase 19'
    Write-Host '5 = Install requirements'
    Write-Host '6 = API status'
    Write-Host '7 = Export OpenAPI schema'
    Write-Host '8 = Open Swagger docs'
    Write-Host '9 = Exit'
    $choice = Read-Host 'Press a number'
    switch ($choice) {
        '1' { & $MyInvocation.MyCommand.Path -Action start -ApiHost $ApiHost -Port $Port; return }
        '2' { & $MyInvocation.MyCommand.Path -Action start-bg -ApiHost $ApiHost -Port $Port; return }
        '3' { & $MyInvocation.MyCommand.Path -Action test; if ($LASTEXITCODE -ne 0) { Read-Host 'Test failed. Press Enter' } }
        '10' { & $MyInvocation.MyCommand.Path -Action smoke; if ($LASTEXITCODE -ne 0) { Read-Host 'Smoke test failed. Press Enter' } }
        '4' { & $MyInvocation.MyCommand.Path -Action verify; if ($LASTEXITCODE -ne 0) { Read-Host 'Verification failed. Press Enter' } }
        '5' { & $MyInvocation.MyCommand.Path -Action install; if ($LASTEXITCODE -ne 0) { Read-Host 'Install failed. Press Enter' } }
        '6' { & $MyInvocation.MyCommand.Path -Action status; Read-Host 'Press Enter' }
        '7' { & $MyInvocation.MyCommand.Path -Action openapi; Read-Host 'Press Enter' }
        '8' { & $MyInvocation.MyCommand.Path -Action docs; Read-Host 'Press Enter' }
        '9' { return }
        default { Write-Host 'Please enter 1-9.' -ForegroundColor Yellow }
    }
}
