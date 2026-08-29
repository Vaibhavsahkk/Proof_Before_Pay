param (
    [Parameter(Mandatory=$true)]
    [string]$CandidateSha,
    [Parameter(Mandatory=$false)]
    [string]$Phase = "phase_1"
)

$ErrorActionPreference = 'Continue'
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$cloneDir = "ProofBeforePay-clone-" + [guid]::NewGuid().ToString("N")
$clonePath = Join-Path $env:TEMP $cloneDir

# Write log outside the repo
$logPath = Join-Path $env:TEMP "clean_clone_log_$cloneDir.txt"

$COMPOSE_PROJECT_NAME = "pbp_clone_$([guid]::NewGuid().ToString('N').Substring(0,8))"
$env:COMPOSE_PROJECT_NAME = $COMPOSE_PROJECT_NAME

$global:hasErrors = $false

function Log {
    param([string]$message)
    Write-Output $message
    $message | Out-File -FilePath $logPath -Append -Encoding utf8
}

function Run-Command {
    param(
        [string]$CmdName,
        [scriptblock]$ScriptBlock
    )
    Log "`n========================================"
    Log "COMMAND: $CmdName"
    Log "========================================"
    
    try {
        $output = & $ScriptBlock *>&1
        foreach ($line in $output) {
            if ($line -ne $null) { Log $line.ToString() }
        }
        $exitCode = $LASTEXITCODE
        Log "EXIT CODE: $exitCode"
        if ($exitCode -ne 0) {
            Log "ERROR: Command failed with exit $exitCode"
            $global:hasErrors = $true
        }
    } catch {
        Log "Exception: $_"
        Log "EXIT CODE: 1"
        $global:hasErrors = $true
    }
}

try {
    Log "--- CLEAN CLONE EXECUTION ($Phase) ---"
    Log "CANDIDATE SHA: $CandidateSha"
    Log "COMPOSE PROJECT: $COMPOSE_PROJECT_NAME"

    Run-Command "git clone" { git clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath }
    if ($global:hasErrors) { throw "Clone failed" }

    Set-Location $clonePath

    Run-Command "git checkout" { git checkout $CandidateSha }
    if ($global:hasErrors) { throw "Checkout failed" }
    
    $headOutput = git rev-parse HEAD 2>&1 | Out-String
    $clonedHead = $headOutput.Trim()
    if ($clonedHead -ne $CandidateSha) {
        Log "ERROR: Cloned HEAD ($clonedHead) does not match Candidate SHA ($CandidateSha)."
        $global:hasErrors = $true
        throw "Head mismatch"
    }

    if ($Phase -eq "phase_1") {
        Run-Command "python scripts/validate_phase1.py" { python scripts/validate_phase1.py }
        if ($global:hasErrors) { throw "validate_phase1 failed" }

        Run-Command "python scripts/verify_manifest.py" { python scripts/verify_manifest.py }
        if ($global:hasErrors) { throw "verify_manifest failed" }

        Run-Command "pytest tests/test_phase1_validation.py tests/test_manifest.py" { pytest tests/test_phase1_validation.py tests/test_manifest.py }
        if ($global:hasErrors) { throw "pytest failed" }
    } else {
        Run-Command ".\scripts\run_adversarial_tests.ps1" { & powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ".\scripts\run_adversarial_tests.ps1" }
        if ($global:hasErrors) { throw "adversarial tests failed" }
    }

    Run-Command ".\verify.ps1" { & powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ".\verify.ps1" }
    if ($global:hasErrors) { throw "verify.ps1 failed" }

    Run-Command "bash ./verify.sh" { & 'C:\Program Files\Git\bin\bash.exe' ./verify.sh }
    if ($global:hasErrors) { throw "verify.sh failed" }

    Run-Command "git diff --check" { git diff --check }
    if ($global:hasErrors) { throw "Dirty tree (diff --check)" }

    Run-Command "git diff --cached --check" { git diff --cached --check }
    if ($global:hasErrors) { throw "Dirty tree (cached)" }

    Run-Command "git status --short" { git status --short }
    if ($global:hasErrors) { throw "Dirty tree (status)" }
    
    $cleanStatusOut = git status --short 2>&1 | Out-String
    if ($cleanStatusOut.Trim() -ne "") {
        Log "ERROR: Post-test clean clone is not empty: $cleanStatusOut"
        throw "Dirty tree"
    }

    Log "`nCLEAN CLONE HARNESS RESULT: PASS"
    Log "ALL CHECKS EXITED 0"

} catch {
    Log "HARNESS ABORTED: $_"
    $global:hasErrors = $true
} finally {
    Set-Location $repoRoot
    
    # Cleanup Docker Compose for this unique project only
    if (Test-Path "$clonePath\docker-compose.yml") {
        Write-Output "Cleaning up docker compose for project $COMPOSE_PROJECT_NAME..."
        & docker compose -f "$clonePath\docker-compose.yml" --project-name $COMPOSE_PROJECT_NAME down --remove-orphans --volumes 2>&1 | Out-Null
    }

    if (Test-Path $clonePath) {
        Remove-Item -Path $clonePath -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Normalize log and copy to repo
    Write-Output "Normalizing and copying log..."
    $content = [System.IO.File]::ReadAllText($logPath)
    $content = $content.Replace("`r`n", "`n")
    $normalizedLines = $content.Split("`n") | ForEach-Object { $_.TrimEnd() }
    
    $dest = "$repoRoot\evidence\$Phase\final_clean_clone_execution.txt"
    $destDir = Split-Path $dest
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
    
    [System.IO.File]::WriteAllLines($dest, $normalizedLines, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "Saved normalized log to $dest"

    if ($global:hasErrors) {
        Write-Output "Clean clone tests failed. Exit 1."
        exit 1
    } else {
        Write-Output "Clean clone tests passed. Exit 0."
        exit 0
    }
}
