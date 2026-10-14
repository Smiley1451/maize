[CmdletBinding()]
param(
    [string]$ApiHost = '127.0.0.1',
    [int]$Port = 8000,
    [switch]$Reload
)
$ErrorActionPreference = 'Stop'
$Base = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $Base
$env:MAIZE_PROJECT_ROOT = $ProjectRoot
$env:LOKY_MAX_CPU_COUNT = if ($env:LOKY_MAX_CPU_COUNT) { $env:LOKY_MAX_CPU_COUNT } else { '4' }
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw 'Python was not found on PATH.' }
Set-Location $Base
Write-Host '==============================================================' -ForegroundColor DarkCyan
Write-Host 'PHASE 19: STARTING FASTAPI BACKEND' -ForegroundColor Cyan
Write-Host "PROJECT ROOT: $ProjectRoot"
Write-Host "API: http://$ApiHost`:$Port"
Write-Host "DOCS: http://$ApiHost`:$Port/docs"
Write-Host 'Press Ctrl+C to stop the server.' -ForegroundColor Yellow
Write-Host '==============================================================' -ForegroundColor DarkCyan
$args = @('-u','-m','uvicorn','app.main:app','--host',$ApiHost,'--port',$Port.ToString())
if ($Reload) { $args += '--reload' }
& $Python.Source @args
exit $LASTEXITCODE
