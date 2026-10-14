[CmdletBinding()]
param([switch]$UpgradePip)
$ErrorActionPreference = 'Stop'
$Base = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { throw 'Python was not found on PATH. Install Python 3.13 and reopen PowerShell.' }
Write-Host 'PHASE 19: INSTALLING FASTAPI BACKEND REQUIREMENTS...' -ForegroundColor Cyan
if ($UpgradePip) { & $Python.Source -m pip install --upgrade pip }
& $Python.Source -m pip install -r (Join-Path $Base 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed with exit code $LASTEXITCODE" }
Write-Host 'FASTAPI BACKEND REQUIREMENTS INSTALLED' -ForegroundColor Green
