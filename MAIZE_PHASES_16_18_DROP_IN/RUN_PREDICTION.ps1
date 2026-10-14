param(
  [Parameter(Mandatory=$true)][string]$InputCsv,
  [string]$OutputCsv=''
)
$ErrorActionPreference='Stop'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$Py=(Get-Command python -ErrorAction Stop).Source
$env:LOKY_MAX_CPU_COUNT=if($env:LOKY_MAX_CPU_COUNT){$env:LOKY_MAX_CPU_COUNT}else{'4'}
$script=Join-Path $Here 'scripts\predict_new.py'
$args=@('-u',$script,'--input',(Resolve-Path $InputCsv).Path)
if($OutputCsv){$args += @('--output',$OutputCsv)}
& $Py @args
if($LASTEXITCODE -ne 0){throw "Prediction engine failed with exit code $LASTEXITCODE"}
