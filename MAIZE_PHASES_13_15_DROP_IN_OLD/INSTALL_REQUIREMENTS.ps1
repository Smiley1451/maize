$ErrorActionPreference = 'Stop'
python -m pip install --upgrade pip
python -m pip install -r "$PSScriptRoot\requirements.txt"
Write-Host "Dependencies installed." -ForegroundColor Green
