$ErrorActionPreference='Stop'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
python -m pip install --upgrade pip
python -m pip install -r (Join-Path $Here 'requirements.txt')
python -c "import pandas,numpy,sklearn,joblib; print('CORE PACKAGES OK')"
