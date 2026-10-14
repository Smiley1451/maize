[CmdletBinding()]
param(
    [ValidateSet('all','verify','status','install','assistant','api','services')]
    [string]$Action = 'all',
    [string]$ProjectRoot = '',
    [switch]$RefreshAIIndex,
    [switch]$StartApi,
    [switch]$NoServiceTabs
)

# ============================================================================
# MAIZE AI/ML DIGITALIZATION PROJECT - UNIFIED MASTER RUNNER
# ============================================================================
# Purpose:
#   One PowerShell command to run/resume the completed project phases, verify
#   the working backend/AI components, and clearly report the remaining Phase 20.
#
# Design goals:
#   - Windows PowerShell 5.1 compatible
#   - ASCII-only PowerShell source to avoid parser/encoding issues
#   - Uses the existing phase runners instead of duplicating phase logic
#   - Respects each phase group's saved state and skips completed work
#   - Uses real process exit codes where available
#   - Checks phase_state files for runners that use state instead of exit codes
#   - Never starts an interactive AI chat during a batch run
#   - Normal -Action all opens dedicated FastAPI and AI assistant tabs at the end
#   - Use -NoServiceTabs to suppress the two service tabs
#   - Never starts the API in the master console unless a service tab is requested
#   - Phase 20 is intentionally reported as PENDING until its implementation
#     is present; no functionality is invented here.
# ============================================================================

$ErrorActionPreference = 'Stop'

# ----- Resolve project root --------------------------------------------------
if ($ProjectRoot -and (Test-Path -LiteralPath $ProjectRoot)) {
    $Root = (Resolve-Path -LiteralPath $ProjectRoot).Path
}
else {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Path
}

if (-not (Test-Path -LiteralPath $Root)) {
    throw "Project root does not exist: $Root"
}

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    throw 'Python was not found on PATH. Install Python 3.13+ and reopen PowerShell.'
}
$PythonExe = $PythonCmd.Source

# Windows ML stability / UTF-8 settings used by the existing project runners.
if (-not $env:LOKY_MAX_CPU_COUNT) { $env:LOKY_MAX_CPU_COUNT = '4' }
$env:PYTHONUTF8 = '1'
$env:MAIZE_PROJECT_ROOT = $Root

$MasterLogDir = Join-Path $Root 'MASTER_RUN_LOGS'
New-Item -ItemType Directory -Force -Path $MasterLogDir | Out-Null
$RunStamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$MasterLog = Join-Path $MasterLogDir "MASTER_RUN_$RunStamp.log"
$StatusFile = Join-Path $MasterLogDir 'MASTER_PROJECT_STATUS.json'

# ----- Console helpers ------------------------------------------------------
function Write-Log {
    param(
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    Write-Host $Message -ForegroundColor $Color
    Add-Content -LiteralPath $MasterLog -Value $Message -Encoding UTF8
}

function Write-Section {
    param([string]$Title)
    $line = '=' * 72
    Write-Log '' DarkGray
    Write-Log $line DarkCyan
    Write-Log $Title Cyan
    Write-Log $line DarkCyan
}

function Test-PathRequired {
    param([string]$RelativePath)
    $p = Join-Path $Root $RelativePath
    return (Test-Path -LiteralPath $p)
}

function Invoke-PowerShellRunner {
    param(
        [Parameter(Mandatory=$true)][string]$ScriptPath,
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        throw "Runner not found: $ScriptPath"
    }

    $displayArgs = ($Arguments -join ' ')
    Write-Log ("RUNNER: {0} {1}" -f $ScriptPath,$displayArgs) DarkGray

    # Run the child PowerShell in the same console so progress is visible.
    # The runner itself manages Python output/logging.
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ScriptPath @Arguments
    $code = $LASTEXITCODE

    if ($code -ne 0) {
        throw "Runner failed with exit code $code : $ScriptPath"
    }
}

function Invoke-PythonScript {
    param(
        [Parameter(Mandatory=$true)][string]$ScriptPath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $Root
    )

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        throw "Python script not found: $ScriptPath"
    }

    Push-Location $WorkingDirectory
    try {
        & $PythonExe -u $ScriptPath @Arguments
        $code = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if ($code -ne 0) {
        throw "Python script failed with exit code $code : $ScriptPath"
    }
}

function Find-Runner {
    param([string[]]$RelativeCandidates)
    foreach ($r in $RelativeCandidates) {
        $p = Join-Path $Root $r
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

# ----- Phase definitions ---------------------------------------------------
$PhaseDefinitions = @(
    [pscustomobject]@{ Phase=1;  Name='Model readiness audit';                         Group='1-9'  },
    [pscustomobject]@{ Phase=2;  Name='Yield baseline models';                         Group='1-9'  },
    [pscustomobject]@{ Phase=3;  Name='TLB + SDM disease models';                     Group='1-9'  },
    [pscustomobject]@{ Phase=4;  Name='PCA + genotype clustering';                    Group='1-9'  },
    [pscustomobject]@{ Phase=5;  Name='Weather risk readiness';                       Group='1-9'  },
    [pscustomobject]@{ Phase=6;  Name='Group-aware hyperparameter tuning';             Group='1-9'  },
    [pscustomobject]@{ Phase=7;  Name='Model explainability';                         Group='1-9'  },
    [pscustomobject]@{ Phase=8;  Name='Model packaging';                              Group='1-9'  },
    [pscustomobject]@{ Phase=9;  Name='Final project verification';                   Group='1-9'  },
    [pscustomobject]@{ Phase=10; Name='Genotype identity review';                     Group='10-12'},
    [pscustomobject]@{ Phase=11; Name='Production dataset construction';              Group='10-12'},
    [pscustomobject]@{ Phase=12; Name='Generalization validation';                    Group='10-12'},
    [pscustomobject]@{ Phase=13; Name='Advanced yield modeling + feature engineering';Group='13-15'},
    [pscustomobject]@{ Phase=14; Name='Advanced TLB + SDM disease modeling';           Group='13-15'},
    [pscustomobject]@{ Phase=15; Name='Multi-trait genotype breeding intelligence';    Group='13-15'},
    [pscustomobject]@{ Phase=16; Name='Weather-driven disease forecasting';            Group='16-18'},
    [pscustomobject]@{ Phase=17; Name='Model explainability + error analysis';         Group='16-18'},
    [pscustomobject]@{ Phase=18; Name='Reusable prediction engine';                   Group='16-18'},
    [pscustomobject]@{ Phase=19; Name='FastAPI backend + automated API testing';       Group='19'   },
    [pscustomobject]@{ Phase=20; Name='Pending project phase';                         Group='20'   },
    [pscustomobject]@{ Phase=21; Name='AI/LLM research assistant + RAG';              Group='21'   }
)

# ----- Existing runner locations ------------------------------------------
$Runner19 = Find-Runner @(
    '19_FASTAPI_BACKEND\RUN_PHASE19.ps1',
    'PHASE19_FASTAPI_BACKEND\RUN_PHASE19.ps1'
)

$Runner21 = Find-Runner @(
    'MAIZE_PHASE21_AI_RESEARCH_ASSISTANT_DROP_IN_V2\RUN_PHASE21.ps1',
    'MAIZE_PHASE21_AI_RESEARCH_ASSISTANT_DROP_IN\RUN_PHASE21.ps1'
)

$Runner1012 = Find-Runner @(
    '10_12_NEXT_PHASES\RUN_PHASES_10_12.ps1',
    'MAIZE_PHASES_10_12_DROP_IN\RUN_PHASES_10_12.ps1'
)

$Runner1315 = Find-Runner @(
    'MAIZE_PHASES_13_15_DROP_IN\RUN_PHASES_13_15.ps1',
    'MAIZE_PHASES_13_15_DROP_IN_V3\RUN_PHASES_13_15.ps1'
)

$Runner1618 = Find-Runner @(
    'MAIZE_PHASES_16_18_DROP_IN\RUN_PHASES_16_18.ps1'
)

$Runner19 = $Runner19
$Runner21 = $Runner21

$Pipeline19 = Find-Runner @('19_FASTAPI_BACKEND\RUN_PHASE19.ps1')
$PipelineMain = Find-Runner @('08_AUTOMATED_PIPELINE\run_pipeline.ps1')

# ----- Status readers -------------------------------------------------------
function Get-Phase1To9Status {
    $statePath = Join-Path $Root '08_AUTOMATED_PIPELINE\pipeline_state.json'
    if (-not (Test-Path -LiteralPath $statePath)) { return 'PENDING' }
    try {
        $s = Get-Content $statePath -Raw | ConvertFrom-Json
        if ([int]$s.last_completed -ge 9) { return 'DONE' }
        if ($s.status -eq 'FAILED') { return 'FAILED' }
        return 'PENDING'
    } catch { return 'PENDING' }
}

function Get-GroupedStatus {
    param(
        [string]$StatePath,
        [int[]]$Phases
    )
    if (-not (Test-Path -LiteralPath $StatePath)) { return 'PENDING' }
    try {
        $s = Get-Content $StatePath -Raw | ConvertFrom-Json
        $allDone = $true
        foreach ($n in $Phases) {
            $done = $false
            if ($s.completed) {
                $done = @($s.completed) -contains [string]$n
            }
            if ($s.status) {
                $prop = [string]$n
                if ($s.status.PSObject.Properties.Name -contains $prop) {
                    $done = ([string]$s.status.$prop -eq 'DONE')
                    if ([string]$s.status.$prop -eq 'FAILED') { return 'FAILED' }
                }
            }
            if (-not $done) { $allDone = $false }
        }
        if ($allDone) { return 'DONE' }
        return 'PENDING'
    } catch { return 'PENDING' }
}

function Get-Phase10To12Status {
    if (-not $Runner1012) { return 'MISSING' }
    $base = Split-Path -Parent $Runner1012
    return Get-GroupedStatus -StatePath (Join-Path $base 'phase_state.json') -Phases @(10,11,12)
}

function Get-Phase13To15Status {
    if (-not $Runner1315) { return 'MISSING' }
    $base = Split-Path -Parent $Runner1315
    return Get-GroupedStatus -StatePath (Join-Path $base 'phase_state.json') -Phases @(13,14,15)
}

function Get-Phase16To18Status {
    if (-not $Runner1618) { return 'MISSING' }
    $base = Split-Path -Parent $Runner1618
    return Get-GroupedStatus -StatePath (Join-Path $base 'phase_state.json') -Phases @(16,17,18)
}

function Get-Phase19Status {
    if (-not $Runner19) { return 'MISSING' }
    return 'DONE'  # Verified by the automated suite below when Action=all/verify.
}

function Get-Phase21Status {
    if (-not $Runner21) { return 'MISSING' }
    $manifest = Join-Path (Split-Path -Parent $Runner21) 'index\index_manifest.json'
    if (-not (Test-Path -LiteralPath $manifest)) { return 'PENDING' }
    try {
        $m = Get-Content $manifest -Raw | ConvertFrom-Json
        $errors = 0
        if ($null -ne $m.errors) { $errors = @($m.errors).Count }
        if ([int]$m.file_count -gt 0 -and [int]$m.chunk_count -gt 0 -and $errors -eq 0) {
            return 'DONE'
        }
    } catch { }
    return 'PENDING'
}

function Get-Phase20Status {
    # No Phase 20 implementation is currently present in the known project tree.
    # Do not invent a phase name, runner, or behavior.
    $knownDirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '(^20_|PHASE.?20|_20_)' }
    if ($knownDirs) {
        $runner = $null
        foreach ($d in $knownDirs) {
            $runner = Get-ChildItem -LiteralPath $d.FullName -File -Filter '*.ps1' -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -match '^RUN.*20.*\.ps1$|^RUN_PHASE20\.ps1$' } |
                Select-Object -First 1
            if ($runner) { break }
        }
        if ($runner) { return 'IMPLEMENTED_RUNNER_FOUND' }
    }
    return 'PENDING'
}

function Show-ProjectStatus {
    Write-Section 'MAIZE PROJECT - UNIFIED STATUS'
    Write-Log ("Project root: {0}" -f $Root) Gray
    Write-Log '' Gray

    $s19 = Get-Phase1To9Status
    $s1012 = Get-Phase10To12Status
    $s1315 = Get-Phase13To15Status
    $s1618 = Get-Phase16To18Status
    $s19b = Get-Phase19Status
    $s20 = Get-Phase20Status
    $s21 = Get-Phase21Status

    foreach ($p in $PhaseDefinitions) {
        switch ($p.Group) {
            '1-9'   { $tag = $s19 }
            '10-12' { $tag = $s1012 }
            '13-15' { $tag = $s1315 }
            '16-18' { $tag = $s1618 }
            '19'    { $tag = $s19b }
            '20'    { $tag = $s20 }
            '21'    { $tag = $s21 }
        }
        $color = [ConsoleColor]::Yellow
        if ($tag -eq 'DONE') { $color = [ConsoleColor]::Green }
        elseif ($tag -eq 'FAILED') { $color = [ConsoleColor]::Red }
        Write-Log ("Phase {0,2}: {1,-50} {2}" -f $p.Phase,$p.Name,$tag) $color
    }

    if ($Runner21) {
        $manifest = Join-Path (Split-Path -Parent $Runner21) 'index\index_manifest.json'
        if (Test-Path -LiteralPath $manifest) {
            try {
                $m = Get-Content $manifest -Raw | ConvertFrom-Json
                $err = if ($null -eq $m.errors) { 0 } else { @($m.errors).Count }
                Write-Log '' Gray
                Write-Log ("Phase 21 index: files={0}; chunks={1}; errors={2}" -f $m.file_count,$m.chunk_count,$err) Gray
            } catch { }
        }
    }

    Write-Log '' Gray
    Write-Log 'Interpretation: the group status marks all phases in a completed group as DONE.' Gray
    Write-Log 'Phase 20 remains PENDING until its actual implementation is present.' Yellow
}

# ----- Run grouped phases ---------------------------------------------------
function Run-Phase1To9 {
    Write-Section 'PHASES 1-9 : CORE AUTOMATED ML PIPELINE'
    if (-not $PipelineMain) { throw 'Missing 08_AUTOMATED_PIPELINE\run_pipeline.ps1' }
    Invoke-PowerShellRunner -ScriptPath $PipelineMain -Arguments @('-Action','all')
    $status = Get-Phase1To9Status
    if ($status -ne 'DONE') { throw "Phases 1-9 did not reach DONE state. Current status: $status" }
    Write-Log 'PHASES 1-9: DONE' Green
}

function Run-Phase10To12 {
    Write-Section 'PHASES 10-12 : IDENTITY REVIEW + PRODUCTION DATA + VALIDATION'
    if (-not $Runner1012) { throw 'Missing Phase 10-12 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner1012 -Arguments @('-Action','all')
    $status = Get-Phase10To12Status
    if ($status -ne 'DONE') { throw "Phases 10-12 did not reach DONE state. Current status: $status" }
    Write-Log 'PHASES 10-12: DONE' Green
}

function Run-Phase13To15 {
    Write-Section 'PHASES 13-15 : ADVANCED MODELING + BREEDING INTELLIGENCE'
    if (-not $Runner1315) { throw 'Missing Phase 13-15 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner1315 -Arguments @('-Action','all')
    $status = Get-Phase13To15Status
    if ($status -ne 'DONE') { throw "Phases 13-15 did not reach DONE state. Current status: $status" }
    Write-Log 'PHASES 13-15: DONE' Green
}

function Run-Phase16To18 {
    Write-Section 'PHASES 16-18 : WEATHER READINESS + EXPLAINABILITY + PREDICTION ENGINE'
    if (-not $Runner1618) { throw 'Missing Phase 16-18 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner1618 -Arguments @('-Action','all')
    $status = Get-Phase16To18Status
    if ($status -ne 'DONE') { throw "Phases 16-18 did not reach DONE state. Current status: $status" }
    Write-Log 'PHASES 16-18: DONE' Green
}

function Run-Phase19 {
    Write-Section 'PHASE 19 : FASTAPI BACKEND + AUTOMATED TESTS'
    if (-not $Runner19) { throw 'Missing Phase 19 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner19 -Arguments @('-Action','test')
    Write-Log 'PHASE 19 TEST SUITE: PASSED' Green
}

function Run-Phase21 {
    Write-Section 'PHASE 21 : AI/LLM RESEARCH ASSISTANT + RAG'
    if (-not $Runner21) { throw 'Missing Phase 21 runner.' }

    $phase21Root = Split-Path -Parent $Runner21
    $manifest = Join-Path $phase21Root 'index\index_manifest.json'

    if ($RefreshAIIndex -or -not (Test-Path -LiteralPath $manifest)) {
        Write-Log 'Building/refreshing Phase 21 project index...' Yellow
        Invoke-PowerShellRunner -ScriptPath $Runner21 -Arguments @('-Action','index')
    }
    else {
        Write-Log 'Phase 21 index already exists; keeping the existing index. Use -RefreshAIIndex to rebuild it.' Gray
    }

    Invoke-PowerShellRunner -ScriptPath $Runner21 -Arguments @('-Action','verify')
    Write-Log 'PHASE 21 VERIFICATION: READY' Green
}

function Verify-Phase1To9 {
    Write-Section 'VERIFY PHASES 1-9'
    if (-not $PipelineMain) { throw 'Missing 08_AUTOMATED_PIPELINE\run_pipeline.ps1' }
    Invoke-PowerShellRunner -ScriptPath $PipelineMain -Arguments @('-Action','run','-Stage','9','-NoInstall')
}

function Verify-Phase10To12 {
    Write-Section 'VERIFY PHASES 10-12'
    if (-not $Runner1012) { throw 'Missing Phase 10-12 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner1012 -Arguments @('-Action','verify')
}

function Verify-Phase13To15 {
    Write-Section 'VERIFY PHASES 13-15'
    if (-not $Runner1315) { throw 'Missing Phase 13-15 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner1315 -Arguments @('-Action','verify')
}

function Verify-Phase16To18 {
    Write-Section 'VERIFY PHASES 16-18'
    if (-not $Runner1618) { throw 'Missing Phase 16-18 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner1618 -Arguments @('-Action','verify')
}

function Verify-Phase19 {
    Write-Section 'VERIFY PHASE 19'
    if (-not $Runner19) { throw 'Missing Phase 19 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner19 -Arguments @('-Action','verify')
}

function Verify-Phase21 {
    Write-Section 'VERIFY PHASE 21'
    if (-not $Runner21) { throw 'Missing Phase 21 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner21 -Arguments @('-Action','verify')
}

# ----- Utilities ------------------------------------------------------------
function Install-AllKnownRequirements {
    Write-Section 'INSTALL KNOWN PROJECT REQUIREMENTS'

    $mainReq = Join-Path $Root '08_AUTOMATED_PIPELINE\requirements.txt'
    if (Test-Path -LiteralPath $mainReq) {
        Write-Log 'Installing Phase 1-9 requirements...' Cyan
        & $PythonExe -m pip install -r $mainReq
        if ($LASTEXITCODE -ne 0) { throw "Main requirements installation failed (exit code $LASTEXITCODE)." }
    }

    $installPairs = @()
    if ($Runner1012) { $installPairs += ,@($Runner1012,'install') }
    if ($Runner1315) { $installPairs += ,@($Runner1315,'install') }
    if ($Runner1618) { $installPairs += ,@($Runner1618,'install') }
    if ($Runner19)   { $installPairs += ,@($Runner19,'install') }
    if ($Runner21)   { $installPairs += ,@($Runner21,'install') }

    foreach ($pair in $installPairs) {
        Write-Log ("Installing requirements via {0}" -f $pair[0]) Cyan
        Invoke-PowerShellRunner -ScriptPath $pair[0] -Arguments @('-Action',$pair[1])
    }

    Write-Log 'Known project requirements processed.' Green
}

function Start-InteractiveAssistant {
    Write-Section 'START PHASE 21 INTERACTIVE AI ASSISTANT'
    if (-not $Runner21) { throw 'Missing Phase 21 runner.' }
    $phase21Root = Split-Path -Parent $Runner21
    $chat = Join-Path $phase21Root 'scripts\run_chat.py'
    if (-not (Test-Path -LiteralPath $chat)) { throw "Interactive assistant script not found: $chat" }

    # Launch Python directly so stdin/stdout remain attached to the terminal.
    # This avoids the ReadToEnd/WaitForExit behavior that can block an interactive chat.
    $oldPath = $env:PYTHONPATH
    $env:PYTHONPATH = "$phase21Root;$Root"
    try {
        & $PythonExe -u $chat
        $code = $LASTEXITCODE
    }
    finally {
        $env:PYTHONPATH = $oldPath
    }
    if ($code -ne 0) { throw "AI assistant exited with code $code" }
}

function Test-WindowsTerminal {
    return [bool](Get-Command wt.exe -ErrorAction SilentlyContinue)
}

function Start-ServiceTabs {
    param(
        [switch]$Force
    )

    Write-Section 'OPEN SERVICE TABS : FASTAPI + AI ASSISTANT'

    if (-not $Runner19) { throw 'Missing Phase 19 runner; cannot open FastAPI tab.' }
    if (-not $Runner21) { throw 'Missing Phase 21 runner; cannot open AI assistant tab.' }

    $phase21Root = Split-Path -Parent $Runner21
    $chatScript = Join-Path $phase21Root 'scripts\run_chat.py'
    if (-not (Test-Path -LiteralPath $chatScript)) {
        throw "Interactive assistant script not found: $chatScript"
    }

    $opened = @()
    $wt = Get-Command wt.exe -ErrorAction SilentlyContinue

    if ($wt) {
        # FastAPI gets its own foreground tab so server logs remain visible.
        & $wt.Source -w 0 new-tab --title 'MAIZE FASTAPI' -- powershell.exe -NoProfile -ExecutionPolicy Bypass -NoExit -File $Runner19 -Action start
        if ($LASTEXITCODE -ne 0) {
            throw "Could not open FastAPI Windows Terminal tab. Exit code: $LASTEXITCODE"
        }
        $opened += 'FastAPI'

        # AI assistant is launched directly so stdin/stdout stay attached to the tab.
        $aiCommand = "`$env:PYTHONPATH='$phase21Root;$Root'; `$env:LOKY_MAX_CPU_COUNT='4'; & '$PythonExe' -u '$chatScript'"
        & $wt.Source -w 0 new-tab --title 'MAIZE AI ASSISTANT' -- powershell.exe -NoProfile -ExecutionPolicy Bypass -NoExit -Command $aiCommand
        if ($LASTEXITCODE -ne 0) {
            throw "Could not open AI assistant Windows Terminal tab. Exit code: $LASTEXITCODE"
        }
        $opened += 'AI Assistant'

        Write-Log 'Opened Windows Terminal tabs:' Green
        Write-Log '  [1] MAIZE FASTAPI - foreground API server' Green
        Write-Log '  [2] MAIZE AI ASSISTANT - interactive chat' Green
        return
    }

    # Fallback when Windows Terminal (wt.exe) is unavailable: open separate
    # PowerShell windows so both services are still independently visible.
    Write-Log 'Windows Terminal (wt.exe) was not found. Opening separate PowerShell windows instead.' Yellow

    Start-Process powershell.exe -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy','Bypass',
        '-NoExit',
        '-File',$Runner19,
        '-Action','start'
    )
    $opened += 'FastAPI'

    $aiCommand = "`$env:PYTHONPATH='$phase21Root;$Root'; `$env:LOKY_MAX_CPU_COUNT='4'; & '$PythonExe' -u '$chatScript'"
    Start-Process powershell.exe -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy','Bypass',
        '-NoExit',
        '-Command',$aiCommand
    )
    $opened += 'AI Assistant'

    Write-Log 'Opened separate PowerShell windows:' Green
    Write-Log '  [1] MAIZE FASTAPI - foreground API server' Green
    Write-Log '  [2] MAIZE AI ASSISTANT - interactive chat' Green
}

function Start-ApiBackground {
    Write-Section 'START PHASE 19 FASTAPI BACKEND IN BACKGROUND'
    if (-not $Runner19) { throw 'Missing Phase 19 runner.' }
    Invoke-PowerShellRunner -ScriptPath $Runner19 -Arguments @('-Action','start-bg')
}

function Save-MasterStatus {
    $payload = [ordered]@{
        generated_at = (Get-Date).ToString('o')
        project_root = $Root
        python = $PythonExe
        phases = @()
    }

    $s19 = Get-Phase1To9Status
    $s1012 = Get-Phase10To12Status
    $s1315 = Get-Phase13To15Status
    $s1618 = Get-Phase16To18Status
    $s19b = Get-Phase19Status
    $s20 = Get-Phase20Status
    $s21 = Get-Phase21Status

    for ($n=1; $n -le 21; $n++) {
        if ($n -le 9) { $tag = $s19 }
        elseif ($n -le 12) { $tag = $s1012 }
        elseif ($n -le 15) { $tag = $s1315 }
        elseif ($n -le 18) { $tag = $s1618 }
        elseif ($n -eq 19) { $tag = $s19b }
        elseif ($n -eq 20) { $tag = $s20 }
        else { $tag = $s21 }
        $def = $PhaseDefinitions | Where-Object { $_.Phase -eq $n } | Select-Object -First 1
        $payload.phases += [ordered]@{ phase=$n; name=$def.Name; status=$tag }
    }

    $payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StatusFile -Encoding UTF8
}

function Final-Report {
    Write-Section 'FINAL UNIFIED PROJECT REPORT'
    Save-MasterStatus
    Show-ProjectStatus

    $pending = @()
    $failed = @()
    $statuses = @{
        '1-9'=$null; '10-12'=$null; '13-15'=$null; '16-18'=$null; '19'=$null; '20'=$null; '21'=$null
    }
    $statuses['1-9']=Get-Phase1To9Status
    $statuses['10-12']=Get-Phase10To12Status
    $statuses['13-15']=Get-Phase13To15Status
    $statuses['16-18']=Get-Phase16To18Status
    $statuses['19']=Get-Phase19Status
    $statuses['20']=Get-Phase20Status
    $statuses['21']=Get-Phase21Status

    foreach ($k in $statuses.Keys) {
        if ($statuses[$k] -eq 'FAILED') { $failed += $k }
        elseif ($statuses[$k] -ne 'DONE') { $pending += $k }
    }

    Write-Log '' Gray
    Write-Log ("Master log: {0}" -f $MasterLog) Gray
    Write-Log ("Master status: {0}" -f $StatusFile) Gray

    if ($failed.Count -gt 0) {
        Write-Log ("PROJECT RUN INCOMPLETE - FAILED GROUPS: {0}" -f ($failed -join ', ')) Red
        return $false
    }
    if ($pending.Count -gt 0) {
        Write-Log ("PROJECT RUN INCOMPLETE - PENDING GROUPS: {0}" -f ($pending -join ', ')) Yellow
        return $false
    }

    Write-Log 'ALL PHASES 1-21: DONE' Green
    return $true
}

# ----- Main -----------------------------------------------------------------
try {
    Write-Section 'MAIZE AI/ML DIGITALIZATION PROJECT - UNIFIED RUNNER'
    Write-Log ("Started: {0}" -f (Get-Date)) Gray
    Write-Log ("Root:    {0}" -f $Root) Gray
    Write-Log ("Python:  {0}" -f $PythonExe) Gray
    Write-Log '' Gray

    switch ($Action) {
        'status' {
            Show-ProjectStatus
            Save-MasterStatus
            exit 0
        }

        'install' {
            Install-AllKnownRequirements
            Save-MasterStatus
            exit 0
        }

        'assistant' {
            Start-InteractiveAssistant
            exit 0
        }

        'api' {
            Start-ApiBackground
            exit 0
        }

        'services' {
            Start-ServiceTabs
            exit 0
        }

        'verify' {
            Verify-Phase1To9
            Verify-Phase10To12
            Verify-Phase13To15
            Verify-Phase16To18
            Verify-Phase19

            $phase20Status = Get-Phase20Status
            if ($phase20Status -eq 'IMPLEMENTED_RUNNER_FOUND') {
                Write-Log 'Phase 20 runner detected, but it was not auto-executed because its contract is not known from the completed project.' Yellow
                Write-Log 'Complete Phase 20 using its own runner before declaring the project final.' Yellow
            }
            else {
                Write-Log 'Phase 20 is still PENDING; no Phase 20 implementation was found.' Yellow
            }

            Verify-Phase21
            if (-not (Final-Report)) { exit 2 }
            exit 0
        }

        'all' {
            Run-Phase1To9
            Run-Phase10To12
            Run-Phase13To15
            Run-Phase16To18
            Run-Phase19

            Write-Section 'PHASE 20 CHECK'
            $phase20Status = Get-Phase20Status
            if ($phase20Status -eq 'IMPLEMENTED_RUNNER_FOUND') {
                Write-Log 'Phase 20 runner detected.' Yellow
                Write-Log 'It was NOT auto-run because its exact command contract is not established in this unified script.' Yellow
                Write-Log 'Run Phase 20 separately, then rerun this master script.' Yellow
            }
            else {
                Write-Log 'Phase 20: PENDING - no implementation/runner found.' Yellow
            }

            Run-Phase21

            if ($StartApi) {
                Start-ApiBackground
            }

            if (-not $NoServiceTabs) {
                Start-ServiceTabs
            }

            if (-not (Final-Report)) { exit 2 }
            exit 0
        }
    }
}
catch {
    Write-Log '' DarkGray
    Write-Log ('MASTER RUN FAILED: {0}' -f $_.Exception.Message) Red
    Save-MasterStatus
    Write-Log ("Master log: {0}" -f $MasterLog) Yellow
    exit 1
}
