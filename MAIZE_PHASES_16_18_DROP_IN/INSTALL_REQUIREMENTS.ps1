$ErrorActionPreference='Stop'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host 'Installing core Python packages...' -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r (Join-Path $Here 'requirements.txt')
Write-Host 'Core packages installed.' -ForegroundColor Green
Write-Host 'Checking optional XGBoost...' -ForegroundColor Cyan
python -c "import xgboost; print('XGBoost available:', xgboost.__version__)"
if($LASTEXITCODE -ne 0){ Write-Host 'XGBoost is optional and was not installed/available. The pipeline will continue without it.' -ForegroundColor Yellow }
