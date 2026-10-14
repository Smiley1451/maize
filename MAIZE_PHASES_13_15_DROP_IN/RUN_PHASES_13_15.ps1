param(
  [ValidateSet('menu','all','next','prev','redo','retry','status','run','install','verify')]
  [string]$Action='menu',
  [ValidateRange(13,15)] [int]$Stage=13
)
$ErrorActionPreference='Continue'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$StatePath=Join-Path $Here 'phase_state.json'
$LogDir=Join-Path $Here 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$env:LOKY_MAX_CPU_COUNT=if($env:LOKY_MAX_CPU_COUNT){$env:LOKY_MAX_CPU_COUNT}else{'4'}
$Stages=@{
  13=[pscustomobject]@{Name='Advanced yield modeling + feature engineering';Script='phase13_advanced_yield.py'}
  14=[pscustomobject]@{Name='Advanced TLB + SDM disease modeling';Script='phase14_advanced_disease.py'}
  15=[pscustomobject]@{Name='Multi-trait genotype breeding intelligence';Script='phase15_breeding_intelligence.py'}
}
function Load-State{
  if(Test-Path $StatePath){try{return Get-Content $StatePath -Raw | ConvertFrom-Json}catch{}}
  return [pscustomobject]@{current=13;last_failed=0;status=[pscustomobject]@{}}
}
function Save-State($s){$s|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $StatePath}
function Set-Status($s,[int]$n,[string]$v){
  if(-not $s.status){$s|Add-Member NoteProperty status ([pscustomobject]@{})}
  $p=[string]$n
  if($s.status.PSObject.Properties.Name -contains $p){$s.status.$p=$v}else{$s.status|Add-Member NoteProperty $p $v}
}
function Show-Status{
  $s=Load-State; Write-Host "`nPHASE 13-15 STATUS"
  foreach($n in 13..15){$v='PENDING';if($s.status -and ($s.status.PSObject.Properties.Name -contains [string]$n)){$v=$s.status.$n};if($n -eq [int]$s.current -and $v -eq 'PENDING'){$v='NEXT'};Write-Host ("Phase {0}. {1,-48} {2}" -f $n,$Stages[[int]$n].Name,$v)}
  Write-Host "State: current=$($s.current); last_failed=$($s.last_failed)"
}
function Find-Python{$cmd=Get-Command python -ErrorAction SilentlyContinue;if(-not $cmd){throw 'Python was not found on PATH. Install Python 3.13+ and reopen PowerShell.'};return $cmd}
function Run-Stage([int]$n){
  if(-not $Stages.ContainsKey($n)){throw "Invalid stage: $n"}
  $s=Load-State;$py=Find-Python;$meta=$Stages[$n];$script=Join-Path $Here ('scripts\'+$meta.Script)
  if(-not(Test-Path $script)){throw "Missing stage script: $script"}
  Write-Host "`n==============================================================" -ForegroundColor Cyan
  Write-Host ("PHASE {0}/15 : {1}" -f $n,$meta.Name) -ForegroundColor Cyan
  Write-Host "==============================================================" -ForegroundColor Cyan
  Write-Host ("RUNNING {0}..." -f $meta.Name) -ForegroundColor Yellow
  $stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$log=Join-Path $LogDir ("phase_{0}_{1}.log" -f $n,$stamp)
  $outFile=Join-Path $env:TEMP ("maize_phase_{0}_{1}_out.txt" -f $n,$stamp);$errFile=Join-Path $env:TEMP ("maize_phase_{0}_{1}_err.txt" -f $n,$stamp)
  $proc=Start-Process -FilePath $py.Source -ArgumentList @('-u',$script) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
  $stdout=if(Test-Path $outFile){Get-Content $outFile -Raw}else{''};$stderr=if(Test-Path $errFile){Get-Content $errFile -Raw}else{''}
  if($stdout){Write-Host $stdout};if($stderr){Write-Host $stderr -ForegroundColor DarkYellow};@($stdout,$stderr)-join "`r`n"|Set-Content -Encoding UTF8 $log
  Remove-Item $outFile,$errFile -Force -ErrorAction SilentlyContinue
  $code=[int]$proc.ExitCode
  if($code -ne 0){Set-Status $s $n 'FAILED';$s.last_failed=$n;Save-State $s;Write-Host ("PHASE {0} FAILED (exit code {1})" -f $n,$code) -ForegroundColor Red;Write-Host "Full log: $log" -ForegroundColor Red;return $false}
  Set-Status $s $n 'DONE';$s.last_failed=0;$s.current=if($n -lt 15){$n+1}else{16};Save-State $s
  Write-Host ("PHASE {0} DONE: {1}" -f $n,$meta.Name) -ForegroundColor Green;Write-Host "Log: $log";return $true
}
function Install-Req{$py=Find-Python;&$py.Source -m pip install -r (Join-Path $Here 'requirements.txt');if($LASTEXITCODE -ne 0){throw 'Dependency installation failed.'}}
function Verify{
  $py=Find-Python;$script=Join-Path $Here 'scripts\verify_phase13_15.py';$stamp=Get-Date -Format 'yyyyMMdd_HHmmss';$log=Join-Path $LogDir ("verify_{0}.log" -f $stamp)
  $outFile=Join-Path $env:TEMP ("maize_verify_{0}_out.txt" -f $stamp);$errFile=Join-Path $env:TEMP ("maize_verify_{0}_err.txt" -f $stamp)
  $proc=Start-Process -FilePath $py.Source -ArgumentList @('-u',$script) -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
  $stdout=if(Test-Path $outFile){Get-Content $outFile -Raw}else{''};$stderr=if(Test-Path $errFile){Get-Content $errFile -Raw}else{''};if($stdout){Write-Host $stdout};if($stderr){Write-Host $stderr -ForegroundColor DarkYellow};@($stdout,$stderr)-join "`r`n"|Set-Content -Encoding UTF8 $log
  Remove-Item $outFile,$errFile -Force -ErrorAction SilentlyContinue;if($proc.ExitCode -ne 0){throw "Verification failed. Log: $log"}
}
function Invoke-Action([string]$a){
  $s=Load-State
  switch($a){
    'menu'{Show-Status;Write-Host "`n1 = Next phase   2 = Previous phase   3 = Redo current/failed phase";Write-Host "4 = Run all remaining phases   5 = Run selected phase   6 = Status";Write-Host "7 = Install requirements   8 = Verify phases 13-15   9 = Exit";$c=Read-Host 'Press a number';switch($c){'1'{Invoke-Action 'next'}'2'{Invoke-Action 'prev'}'3'{Invoke-Action 'redo'}'4'{Invoke-Action 'all'}'5'{$st=[int](Read-Host 'Stage (13-15)');Run-Stage $st|Out-Null;Invoke-Action 'menu'}'6'{Show-Status;Invoke-Action 'menu'}'7'{Install-Req;Invoke-Action 'menu'}'8'{Verify;Invoke-Action 'menu'}'9'{return}default{Write-Host 'Invalid choice.' -ForegroundColor Red;Invoke-Action 'menu'}}}
    'status'{Show-Status}
    'install'{Install-Req}
    'verify'{Verify}
    'run'{Run-Stage $Stage|Out-Null}
    'next'{$n=[int]$s.current;if($n -gt 15){Write-Host 'All phases are already done.'}else{Run-Stage $n|Out-Null}}
    'prev'{$n=[int]$s.current-1;if($n -lt 13){Write-Host 'Already at first phase.'}else{Run-Stage $n|Out-Null}}
    'redo'{$n=if([int]$s.last_failed -ge 13){[int]$s.last_failed}elseif([int]$s.current -le 15){[int]$s.current}else{15};Run-Stage $n|Out-Null}
    'retry'{Invoke-Action 'redo'}
    'all'{for($n=[int]$s.current;$n -le 15;$n++){if(-not(Run-Stage $n)){break};$s=Load-State}}
  }
}
try{Invoke-Action $Action}catch{Write-Host $_ -ForegroundColor Red;exit 1}
