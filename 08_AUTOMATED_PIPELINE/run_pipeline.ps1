param(
  [ValidateSet('interactive','next','prev','redo','all','run','retry','status')]
  [string]$Action = 'interactive',
  [int]$Stage = 0,
  [switch]$NoInstall
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Scripts = Join-Path $Root 'scripts'
$LogDir = Join-Path $Root 'logs'
$StateFile = Join-Path $Root 'pipeline_state.json'
$ReqFile = Join-Path $Root 'requirements.txt'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Stages = @{
  1 = @{Name='Model readiness audit'; Script='stage_01_readiness.py'}
  2 = @{Name='Yield baseline models'; Script='stage_02_yield_baseline.py'}
  3 = @{Name='TLB + SDM disease models'; Script='stage_03_disease_models.py'}
  4 = @{Name='PCA + genotype clustering'; Script='stage_04_clustering.py'}
  5 = @{Name='Weather risk readiness'; Script='stage_05_weather_readiness.py'}
  6 = @{Name='Group-aware hyperparameter tuning'; Script='stage_06_tuning.py'}
  7 = @{Name='Model explainability'; Script='stage_07_explainability.py'}
  8 = @{Name='Model packaging'; Script='stage_08_packaging.py'}
  9 = @{Name='Final project verification'; Script='stage_09_verify.py'}
}

function Find-Python {
  $cmd = Get-Command python -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command py -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  throw 'Python was not found. Install Python and make sure python.exe is on PATH.'
}

$Python = Find-Python

function Load-State {
  if (Test-Path $StateFile) {
    try { return (Get-Content $StateFile -Raw | ConvertFrom-Json) } catch { }
  }
  return [pscustomobject]@{current=1; last_completed=0; last_failed=0; status='NEW'}
}

function Save-State($state) {
  $state | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $StateFile
}

function Ensure-Dependencies {
  if ($NoInstall) { return }
  & $Python -c "import pandas,numpy,sklearn,joblib,matplotlib" 2>$null
  if ($LASTEXITCODE -eq 0) { return }
  Write-Host "`n[SETUP] Required Python packages are missing. Installing from requirements.txt..." -ForegroundColor Yellow
  & $Python -m pip install -r $ReqFile
  if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Run: python -m pip install -r 08_AUTOMATED_PIPELINE\requirements.txt' }
}

function Run-Stage([int]$n) {
  if (-not $Stages.ContainsKey($n)) { throw "Unknown stage: $n" }
  $info = $Stages[$n]
  $script = Join-Path $Scripts $info.Script
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $log = Join-Path $LogDir "stage_${n}_${stamp}.log"
  $state = Load-State
  $state.current = $n
  $state.status = 'RUNNING'
  Save-State $state
  Write-Host "`n==============================================================" -ForegroundColor Cyan
  Write-Host "STEP $n/9 : $($info.Name)" -ForegroundColor Cyan
  Write-Host "==============================================================" -ForegroundColor Cyan
  Write-Host "RUNNING $($info.Name)..." -ForegroundColor White
  & $Python $script 2>&1 | Tee-Object -FilePath $log
  if ($LASTEXITCODE -eq 0) {
    $state = Load-State
    $state.last_completed = $n
    $state.current = $n + 1
    $state.last_failed = 0
    $state.status = 'DONE'
    Save-State $state
    Write-Host "STEP $n DONE: $($info.Name)" -ForegroundColor Green
    Write-Host "Log: $log"
    return $true
  }
  $state = Load-State
  $state.last_failed = $n
  $state.status = 'FAILED'
  Save-State $state
  Write-Host "STEP $n FAILED: $($info.Name)" -ForegroundColor Red
  Write-Host "Log: $log"
  Write-Host "Choose RETRY (3) or inspect the log before continuing." -ForegroundColor Yellow
  return $false
}

function Show-Status {
  $state=Load-State
  Write-Host "`nPROJECT PIPELINE STATUS" -ForegroundColor Cyan
  for ($i=1; $i -le 9; $i++) {
    $done = $i -le [int]$state.last_completed
    $mark = if ($done) {'DONE'} elseif ($i -eq [int]$state.current) {'NEXT'} else {'PENDING'}
    Write-Host ("{0}. {1,-36} {2}" -f $i,$Stages[$i].Name,$mark)
  }
  Write-Host "State: $($state.status); current=$($state.current); last_failed=$($state.last_failed)"
}

function Interactive {
  Ensure-Dependencies
  while ($true) {
    Show-Status
    Write-Host "`n1 = Next step   2 = Previous step   3 = Redo current/failed step" -ForegroundColor White
    Write-Host "4 = Run all remaining   5 = Run selected step   6 = Retry failed" -ForegroundColor White
    Write-Host "7 = Status      8 = Exit" -ForegroundColor White
    $choice = Read-Host 'Press a number'
    switch ($choice) {
      '1' {
        $s=[int](Load-State).current
        if ($s -gt 9) { Write-Host 'All steps completed.' -ForegroundColor Green } else { Run-Stage $s | Out-Null }
      }
      '2' {
        $s=[int](Load-State).current - 1
        if ($s -lt 1) { Write-Host 'Already at first step.' } else { $st=Load-State; $st.current=$s; Save-State $st; Write-Host "Moved back to step $s. Press 1 to run it." }
      }
      '3' {
        $st=Load-State; $s=[int]$st.last_failed; if ($s -lt 1) {$s=[int]$st.last_completed}; if ($s -lt 1) {$s=1}; Run-Stage $s | Out-Null
      }
      '4' {
        $s=[int](Load-State).current
        for ($i=$s; $i -le 9; $i++) { if (-not (Run-Stage $i)) { break } }
      }
      '5' {
        $raw=Read-Host 'Enter stage number 1-9'; $s=0; if([int]::TryParse($raw,[ref]$s) -and $s -ge 1 -and $s -le 9){Run-Stage $s | Out-Null}else{Write-Host 'Invalid stage.' -ForegroundColor Yellow}
      }
      '6' {
        $st=Load-State; $s=[int]$st.last_failed
        if ($s -lt 1) { Write-Host 'No failed step recorded.' -ForegroundColor Green } else { Run-Stage $s | Out-Null }
      }
      '7' { Show-Status }
      '8' { return }
      default { Write-Host 'Invalid choice.' -ForegroundColor Yellow }
    }
  }
}

Ensure-Dependencies
switch ($Action) {
  'interactive' { Interactive }
  'next' { $s=[int](Load-State).current; if($s -le 9){Run-Stage $s | Out-Null}else{Write-Host 'All steps completed.'} }
  'prev' { $st=Load-State; $st.current=[Math]::Max(1,[int]$st.current-1); Save-State $st; Write-Host "Current step is now $($st.current)." }
  'redo' { $st=Load-State; $s=[int]$st.last_failed; if($s -lt 1){$s=[int]$st.last_completed}; if($s -lt 1){$s=1}; Run-Stage $s | Out-Null }
  'all' { $s=[int](Load-State).current; for($i=$s;$i -le 9;$i++){if(-not (Run-Stage $i)){exit 2}} }
  'run' { if($Stage -lt 1 -or $Stage -gt 9){throw 'Use -Stage 1..9 with -Action run.'}; Run-Stage $Stage | Out-Null }
  'retry' { $st=Load-State; $s=[int]$st.last_failed; if($s -lt 1){throw 'No failed step to retry.'}; Run-Stage $s | Out-Null }
  'status' { Show-Status }
}
