param(
  [ValidateSet('menu','all','next','prev','redo','status','run','install','verify')]
  [string]$Action='menu',
  [ValidateSet(10,11,12)]
  [int]$Stage=10
)

$ErrorActionPreference='Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $Here
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if(-not $PythonCmd){ throw 'Python was not found. Install Python 3.13+ and ensure python is on PATH.' }

# Keep Joblib/Loky stable on Windows and prevent harmless native stderr from becoming a PowerShell error.
$env:LOKY_MAX_CPU_COUNT='4'
$env:PYTHONUTF8='1'
if(Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue){
  $PSNativeCommandUseErrorActionPreference=$false
}

$StateFile = Join-Path $Here 'phase_state.json'
$LogDir = Join-Path $Here 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Stages = @{
  10=@{Name='Genotype identity review'; Script='phase10_genotype_review.py'}
  11=@{Name='Production dataset construction'; Script='phase11_production_datasets.py'}
  12=@{Name='Generalization validation'; Script='phase12_generalization_validation.py'}
}

function Load-State {
  if(Test-Path $StateFile){ return (Get-Content $StateFile -Raw | ConvertFrom-Json) }
  return [pscustomobject]@{state='NEW'; current=10; completed=@(); last_failed=0}
}
function Save-State($s){ $s | ConvertTo-Json -Depth 5 | Set-Content $StateFile -Encoding UTF8 }
function Status {
  $s=Load-State
  Write-Host ''
  Write-Host 'PHASE 10-12 STATUS' -ForegroundColor Cyan
  foreach($i in 10..12){
    $done=@($s.completed) -contains "$i"
    $tag= if($done){'DONE'} elseif($i -eq [int]$s.current){'NEXT'} else {'PENDING'}
    Write-Host ("Phase {0}. {1,-34} {2}" -f $i,$Stages[$i].Name,$tag)
  }
  Write-Host ("State: {0}; current={1}; last_failed={2}" -f $s.state,$s.current,$s.last_failed)
  Write-Host ''
}
function Run-Stage([int]$n){
  $s=Load-State
  $name=$Stages[$n].Name
  $script=Join-Path $Here ('scripts\'+$Stages[$n].Script)
  if(-not (Test-Path $script)){ throw "Missing stage script: $script" }
  $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
  $log=Join-Path $LogDir ("phase_{0}_{1}.log" -f $n,$stamp)
  Write-Host ''
  Write-Host ('='*62) -ForegroundColor DarkGray
  Write-Host ("PHASE {0}/12 : {1}" -f $n,$name) -ForegroundColor Yellow
  Write-Host ('='*62) -ForegroundColor DarkGray
  Write-Host ("RUNNING {0}..." -f $name) -ForegroundColor Green
  try{
    # Windows PowerShell 5.1 can surface a Python warning written to stderr as a
    # NativeCommandError even when Python exits successfully. Temporarily use a
    # non-terminating native-command error preference, then rely on the actual
    # process exit code to determine success/failure.
    $oldNativePreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
      & $PythonCmd.Source -u $script 2>&1 | Tee-Object -FilePath $log
      $exitCode=$LASTEXITCODE
    } finally {
      $ErrorActionPreference = $oldNativePreference
    }
    if($exitCode -ne 0){ throw "Python exited with code $exitCode" }
    if(-not (@($s.completed) -contains "$n")){ $s.completed=@($s.completed)+"$n" }
    $s.last_failed=0
    if($n -lt 12){ $s.current=$n+1; $s.state='DONE' } else { $s.current=13; $s.state='DONE' }
    Save-State $s
    Write-Host ("PHASE {0} DONE: {1}" -f $n,$name) -ForegroundColor Green
    Write-Host "Log: $log"
  } catch {
    $s.last_failed=$n; $s.current=$n; $s.state='FAILED'; Save-State $s
    Write-Host ("PHASE {0} FAILED: {1}" -f $n,$_.Exception.Message) -ForegroundColor Red
    Write-Host "Log: $log"
    throw
  }
}
function Ensure-Phase([int]$n){
  if($n -eq 11 -and -not (Test-Path (Join-Path $Here 'outputs\PHASE_10_GENOTYPE_REVIEW\GENOTYPE_IDENTITY_DOMAIN_MASTER.csv'))){ Run-Stage 10 }
  if($n -eq 12 -and -not (Test-Path (Join-Path $Here 'outputs\PHASE_11_PRODUCTION_DATASETS\YIELD_PRODUCTION_STRICT.csv'))){ Run-Stage 11 }
}
function Install-Requirements{
  $req=Join-Path $Here 'requirements.txt'
  Write-Host 'INSTALLING PHASE 10-12 PYTHON REQUIREMENTS...' -ForegroundColor Yellow
  & $PythonCmd.Source -m pip install -r $req
  if($LASTEXITCODE -ne 0){ throw "pip exited with code $LASTEXITCODE" }
  Write-Host 'PHASE 10-12 REQUIREMENTS READY' -ForegroundColor Green
}
function Menu {
  Status
  Write-Host '1 = Next phase'
  Write-Host '2 = Previous phase'
  Write-Host '3 = Redo current/failed phase'
  Write-Host '4 = Run all remaining phases'
  Write-Host '5 = Run selected phase'
  Write-Host '6 = Status'
  Write-Host '7 = Install requirements'
  Write-Host '8 = Verify phases 10-12'
  Write-Host '9 = Exit'
  $pick=Read-Host 'Press a number'
  switch($pick){
    '1' { & $PSCommandPath -Action next }
    '2' { & $PSCommandPath -Action prev }
    '3' { & $PSCommandPath -Action redo }
    '4' { & $PSCommandPath -Action all }
    '5' { $st=[int](Read-Host 'Enter phase 10, 11 or 12'); & $PSCommandPath -Action run -Stage $st }
    '6' { Status }
    '7' { Install-Requirements }
    '8' { & $PSCommandPath -Action verify }
    default { }
  }
}

switch($Action){
  'status' { Status }
  'install' { Install-Requirements }
  'verify' { & $PythonCmd.Source -u (Join-Path $Here 'scripts\verify_phase10_12.py'); if($LASTEXITCODE -ne 0){ throw "Verification failed with code $LASTEXITCODE" } }
  'run' { Ensure-Phase $Stage; Run-Stage $Stage }
  'all' {
    $s=Load-State
    for($i=10;$i -le 12;$i++){
      if(@($s.completed) -contains "$i"){ Write-Host ("PHASE {0} ALREADY DONE - skipping" -f $i) -ForegroundColor DarkGray; continue }
      Run-Stage $i
      $s=Load-State
    }
  }
  'next' {
    $s=Load-State; $n=[int]$s.current
    if($n -gt 12){ Write-Host 'All phases already completed.'; break }
    Ensure-Phase $n; Run-Stage $n
  }
  'prev' {
    $s=Load-State; $n=[int]$s.current-1
    if($n -lt 10){ throw 'Already at first phase.' }
    Run-Stage $n
  }
  'redo' {
    $s=Load-State
    if([int]$s.last_failed -gt 0){ $n=[int]$s.last_failed }
    elseif([int]$s.current -gt 12){ $n=12 }
    else { $n=[int]$s.current }
    Run-Stage $n
  }
  'menu' { Menu }
}
