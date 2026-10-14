param(
    [ValidateSet('menu','index','chat','test','eval','verify','status','rebuild','install')]
    [string]$Action='menu'
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $Root
$Python = Get-Command python -ErrorAction SilentlyContinue

if (-not $Python) {
    throw 'Python was not found on PATH. Install Python 3.11+ and reopen PowerShell.'
}

$env:PYTHONPATH = "$Root;$ProjectRoot"
if (-not $env:LOKY_MAX_CPU_COUNT) { $env:LOKY_MAX_CPU_COUNT = '4' }

function Run-Python([string]$ScriptName, [string[]]$Args = @()) {
    $scriptPath = Join-Path $Root ("scripts\" + $ScriptName)
    if (-not (Test-Path $scriptPath)) {
        throw "Python script not found: $scriptPath"
    }

    $logDir = Join-Path $Root 'logs'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $log = Join-Path $logDir ("$($ScriptName -replace '\.py$','')_$stamp.log")

    Write-Host "============================================================" -ForegroundColor DarkGray
    Write-Host "RUNNING $ScriptName" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkGray

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Python.Source
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $argText = @('"' + $scriptPath + '"')
    foreach ($a in $Args) {
        $escaped = [string]$a -replace '"','\"'
        $argText += ('"' + $escaped + '"')
    }
    $psi.Arguments = ($argText -join ' ')

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()

    $stdout = $stdoutTask.Result
    $stderr = $stderrTask.Result
    $combined = $stdout
    if ($stderr) {
        if ($combined) { $combined += "`r`n" }
        $combined += $stderr
    }

    $combined | Tee-Object -FilePath $log | Write-Host

    if ($process.ExitCode -ne 0) {
        Write-Host "FAILED: $ScriptName (exit code $($process.ExitCode))" -ForegroundColor Red
        Write-Host "Log: $log" -ForegroundColor Yellow
        throw "Phase 21 script failed: $ScriptName"
    }

    Write-Host "DONE: $ScriptName" -ForegroundColor Green
    Write-Host "Log: $log" -ForegroundColor DarkGray
}

function Install-Deps {
    Write-Host 'Installing Phase 21 Python dependencies...' -ForegroundColor Cyan
    $args = @('-m','pip','install','-r',(Join-Path $Root 'requirements.txt'))
    $p = Start-Process -FilePath $Python.Source -ArgumentList $args -NoNewWindow -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "Dependency installation failed (exit code $($p.ExitCode))." }
    Write-Host 'Dependencies installed.' -ForegroundColor Green
}

function Status {
    $manifestPath = Join-Path $Root 'index\index_manifest.json'
    Write-Host ''
    Write-Host 'PHASE 21 STATUS' -ForegroundColor Yellow
    if (Test-Path $manifestPath) {
        $json = Get-Content $manifestPath -Raw | ConvertFrom-Json
        $errorCount = 0
        if ($null -ne $json.errors) { $errorCount = @($json.errors).Count }
        Write-Host "Indexed files : $($json.file_count)"
        Write-Host "Indexed chunks: $($json.chunk_count)"
        Write-Host "Index errors  : $errorCount"
        Write-Host "Built at      : $($json.built_at)"
    }
    else {
        Write-Host 'Index status  : NOT BUILT' -ForegroundColor Yellow
    }
}

switch ($Action) {
    'index'   { Run-Python 'build_index.py' }
    'chat'    { Run-Python 'run_chat.py' }
    'test'    { Run-Python 'verify_phase21.py' }
    'eval'    { Run-Python 'run_eval.py' }
    'verify'  {
        Run-Python 'verify_phase21.py'
        Run-Python 'run_eval.py'
        Write-Host 'PHASE 21 COMPLETE VERIFICATION: DONE' -ForegroundColor Green
    }
    'status'  { Status }
    'rebuild' {
        $indexDir = Join-Path $Root 'index'
        if (Test-Path $indexDir) {
            Get-ChildItem -Path $indexDir -Filter '*.json*' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
        }
        Run-Python 'build_index.py'
    }
    'install' { Install-Deps }
    'menu' {
        while ($true) {
            Write-Host ''
            Write-Host '============================================================' -ForegroundColor Yellow
            Write-Host 'PHASE 21 - MAIZE AI/LLM RESEARCH ASSISTANT' -ForegroundColor Yellow
            Write-Host '============================================================' -ForegroundColor Yellow
            Write-Host '1 = Build/refresh project index'
            Write-Host '2 = Start interactive AI assistant'
            Write-Host '3 = Run full automated test suite'
            Write-Host '4 = Verify and evaluate everything'
            Write-Host '5 = Status'
            Write-Host '6 = Install requirements'
            Write-Host '7 = Rebuild index from scratch'
            Write-Host '8 = Exit'
            $choice = Read-Host 'Press a number'
            if ($choice -eq '8') { break }
            try {
                switch ($choice) {
                    '1' { Run-Python 'build_index.py' }
                    '2' { Run-Python 'run_chat.py' }
                    '3' { Run-Python 'verify_phase21.py' }
                    '4' { Run-Python 'verify_phase21.py'; Run-Python 'run_eval.py' }
                    '5' { Status }
                    '6' { Install-Deps }
                    '7' { & $MyInvocation.MyCommand.Path -Action rebuild }
                    default { Write-Host 'Invalid option.' -ForegroundColor Red }
                }
            }
            catch {
                Write-Host $_ -ForegroundColor Red
            }
        }
    }
}
