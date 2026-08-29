param (
    [Parameter(Mandatory = $false)]
    [string]$CandidateSha,

    [Parameter(Mandatory = $false)]
    [ValidateSet("phase_0", "phase_1", "phase_2")]
    [string]$Phase = "phase_1",

    [Parameter(Mandatory = $false)]
    [switch]$SelfTestFailClosed
)

$ErrorActionPreference = "Continue"

if ($SelfTestFailClosed) {
    & powershell.exe -NonInteractive -NoProfile -Command "exit 7"
    $forcedExit = $LASTEXITCODE
    Write-Output "FAIL-CLOSED SELF-TEST INNER EXIT: $forcedExit"
    if ($forcedExit -eq 0) {
        Write-Error "Fail-closed self-test did not produce a non-zero exit."
        exit 2
    }
    Write-Output "FAIL-CLOSED SELF-TEST RESULT: EXPECTED FAILURE"
    exit 1
}

if ($CandidateSha -notmatch "^[0-9a-fA-F]{40}$") {
    Write-Error "CandidateSha must be an exact 40-character Git commit SHA."
    exit 2
}

$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$cloneName = "ProofBeforePay-clone-" + [guid]::NewGuid().ToString("N")
$clonePath = Join-Path $env:TEMP $cloneName
$logPath = Join-Path $env:TEMP "clean_clone_log_$cloneName.txt"
$composeProjectName = "pbp_clone_$([guid]::NewGuid().ToString('N').Substring(0, 8))"
$previousComposeProjectName = [Environment]::GetEnvironmentVariable("COMPOSE_PROJECT_NAME", "Process")
$hadComposeProjectName = $null -ne $previousComposeProjectName
$env:COMPOSE_PROJECT_NAME = $composeProjectName
$script:hasErrors = $false

function Write-Log {
    param([string]$Message)

    Write-Output $Message
    $Message | Out-File -FilePath $logPath -Append -Encoding utf8
}

function Invoke-LoggedCommand {
    param(
        [string]$Name,
        [scriptblock]$Command,
        [int]$ExpectedExit = 0,
        [string]$RequiredOutputLine = ""
    )

    Write-Log ""
    Write-Log "========================================"
    Write-Log "COMMAND: $Name"
    Write-Log "EXPECTED EXIT CODE: $ExpectedExit"
    Write-Log "========================================"

    try {
        $output = @(& $Command *>&1)
        $exitCode = $LASTEXITCODE
        $renderedOutput = @()
        foreach ($line in $output) {
            if ($null -ne $line) {
                $renderedLine = $line.ToString()
                $renderedOutput += $renderedLine
                Write-Log $renderedLine
            }
        }
        Write-Log "EXIT CODE: $exitCode"
        if ($exitCode -ne $ExpectedExit) {
            Write-Log "ERROR: Expected exit $ExpectedExit but observed $exitCode."
            $script:hasErrors = $true
        }
        if ($RequiredOutputLine -ne "" -and $RequiredOutputLine -notin $renderedOutput) {
            Write-Log "ERROR: Required output line was not observed: $RequiredOutputLine"
            $script:hasErrors = $true
        }
    }
    catch {
        Write-Log "EXCEPTION: $_"
        Write-Log "EXIT CODE: 1"
        $script:hasErrors = $true
    }
}

try {
    Write-Log "--- CLEAN CLONE EXECUTION ($Phase) ---"
    Write-Log "CANDIDATE SHA: $CandidateSha"
    Write-Log "COMPOSE PROJECT: $composeProjectName"
    Write-Log "CLONE PATH: $clonePath"

    Invoke-LoggedCommand "fail-closed harness self-test" {
        & powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath -CandidateSha $CandidateSha -Phase $Phase -SelfTestFailClosed
    } -ExpectedExit 1
    if ($script:hasErrors) {
        throw "Fail-closed harness self-test failed."
    }

    Invoke-LoggedCommand "git clone" {
        git clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath
    }
    if ($script:hasErrors) {
        throw "Clone failed."
    }

    Set-Location $clonePath

    Invoke-LoggedCommand "git checkout $CandidateSha" {
        git checkout $CandidateSha
    }
    if ($script:hasErrors) {
        throw "Checkout failed."
    }

    $clonedHead = (git rev-parse HEAD 2>&1 | Out-String).Trim()
    $headExit = $LASTEXITCODE
    Write-Log "OBSERVED CLONED HEAD: $clonedHead"
    Write-Log "GIT REV-PARSE EXIT CODE: $headExit"
    if ($headExit -ne 0 -or $clonedHead -ne $CandidateSha) {
        $script:hasErrors = $true
        throw "Cloned HEAD does not exactly match CandidateSha."
    }

    Invoke-LoggedCommand "git show --check candidate" {
        git show --check --oneline --no-renames $CandidateSha
    }
    if ($script:hasErrors) {
        throw "Candidate commit whitespace validation failed."
    }

    if ($Phase -eq "phase_1") {
        Invoke-LoggedCommand "python scripts/validate_phase1.py" {
            python scripts/validate_phase1.py
        }
        if ($script:hasErrors) {
            throw "Phase 1 validator failed."
        }

        Invoke-LoggedCommand "python scripts/verify_manifest.py" {
            python scripts/verify_manifest.py
        }
        if ($script:hasErrors) {
            throw "Manifest verifier failed."
        }

        Invoke-LoggedCommand "pytest focused Phase 1 suite" {
            python -m pytest tests/test_phase1_validation.py tests/test_manifest.py -q
        }
        if ($script:hasErrors) {
            throw "Focused Phase 1 tests failed."
        }
    }
    elseif ($Phase -eq "phase_0") {
        Invoke-LoggedCommand ".\scripts\run_adversarial_tests.ps1" {
            & powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ".\scripts\run_adversarial_tests.ps1"
        }
        if ($script:hasErrors) {
            throw "Phase 0 adversarial tests failed."
        }
    }
    else {
        Invoke-LoggedCommand "python scripts/verify_manifest.py" {
            python scripts/verify_manifest.py
        }
        if ($script:hasErrors) {
            throw "Manifest verifier failed."
        }

        Invoke-LoggedCommand "pytest focused Phase 2 suite" {
            python -m pytest tests/test_phase2_baseline.py -q
        }
        if ($script:hasErrors) {
            throw "Focused Phase 2 tests failed."
        }

        Invoke-LoggedCommand "missing-key baseline rejection" {
            & powershell.exe -NonInteractive -NoProfile -Command @'
Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue
python -m baseline.run_baseline
exit $LASTEXITCODE
'@
        } -ExpectedExit 1 -RequiredOutputLine "Error: GEMINI_API_KEY environment variable is not set."
        if ($script:hasErrors) {
            throw "Missing-key baseline rejection failed."
        }
    }

    Invoke-LoggedCommand ".\verify.ps1" {
        & powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File ".\verify.ps1"
    }
    if ($script:hasErrors) {
        throw "verify.ps1 failed."
    }

    Invoke-LoggedCommand "bash ./verify.sh" {
        & "C:\Program Files\Git\bin\bash.exe" ./verify.sh
    }
    if ($script:hasErrors) {
        throw "verify.sh failed."
    }

    Invoke-LoggedCommand "git diff --check" {
        git diff --check
    }
    if ($script:hasErrors) {
        throw "git diff --check failed."
    }

    Invoke-LoggedCommand "git diff --cached --check" {
        git diff --cached --check
    }
    if ($script:hasErrors) {
        throw "git diff --cached --check failed."
    }

    Invoke-LoggedCommand "git status --short" {
        git status --short
    }
    if ($script:hasErrors) {
        throw "git status failed."
    }

    $cleanStatus = (git status --short 2>&1 | Out-String).Trim()
    $cleanStatusExit = $LASTEXITCODE
    Write-Log "POST-TEST STATUS EXIT CODE: $cleanStatusExit"
    Write-Log "POST-TEST STATUS OUTPUT: $cleanStatus"
    if ($cleanStatusExit -ne 0 -or $cleanStatus -ne "") {
        $script:hasErrors = $true
        throw "Post-test clean clone is not clean."
    }

    Write-Log ""
    Write-Log "CLEAN CLONE TEST RESULT: PASS"
}
catch {
    Write-Log "HARNESS ABORTED: $_"
    $script:hasErrors = $true
}
finally {
    Set-Location $repoRoot

    $composeFile = Join-Path $clonePath "docker-compose.yml"
    if (Test-Path -LiteralPath $composeFile) {
        Invoke-LoggedCommand "exact-project docker compose down --remove-orphans" {
            docker compose -f $composeFile --project-name $composeProjectName down --remove-orphans
        }
    }

    Invoke-LoggedCommand "verify exact-project containers removed" {
        docker ps -a --filter "label=com.docker.compose.project=$composeProjectName" --format "{{.ID}}"
    }
    $remainingContainers = (docker ps -a --filter "label=com.docker.compose.project=$composeProjectName" --format "{{.ID}}" 2>&1 | Out-String).Trim()
    $containerQueryExit = $LASTEXITCODE
    Write-Log "REMAINING PROJECT CONTAINERS: $remainingContainers"
    if ($containerQueryExit -ne 0 -or $remainingContainers -ne "") {
        $script:hasErrors = $true
        Write-Log "ERROR: Exact-project containers remain after cleanup."
    }

    Invoke-LoggedCommand "verify exact-project networks removed" {
        docker network ls --filter "label=com.docker.compose.project=$composeProjectName" --format "{{.ID}}"
    }
    $remainingNetworks = (docker network ls --filter "label=com.docker.compose.project=$composeProjectName" --format "{{.ID}}" 2>&1 | Out-String).Trim()
    $networkQueryExit = $LASTEXITCODE
    Write-Log "REMAINING PROJECT NETWORKS: $remainingNetworks"
    if ($networkQueryExit -ne 0 -or $remainingNetworks -ne "") {
        $script:hasErrors = $true
        Write-Log "ERROR: Exact-project networks remain after cleanup."
    }

    $tempRoot = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
    $resolvedClonePath = [System.IO.Path]::GetFullPath($clonePath)
    if (-not $resolvedClonePath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        $script:hasErrors = $true
        Write-Log "ERROR: Refusing cleanup outside the validated TEMP root: $resolvedClonePath"
    }
    elseif (Test-Path -LiteralPath $resolvedClonePath) {
        try {
            Remove-Item -LiteralPath $resolvedClonePath -Recurse -Force -ErrorAction Stop
        }
        catch {
            $script:hasErrors = $true
            Write-Log "ERROR: Exact clone cleanup failed: $_"
        }
    }
    if (Test-Path -LiteralPath $resolvedClonePath) {
        $script:hasErrors = $true
        Write-Log "ERROR: Exact clone path still exists after cleanup: $clonePath"
    }
    else {
        Write-Log "EXACT CLONE PATH REMOVED: PASS"
    }

    if ($hadComposeProjectName) {
        $env:COMPOSE_PROJECT_NAME = $previousComposeProjectName
    }
    else {
        Remove-Item Env:COMPOSE_PROJECT_NAME -ErrorAction SilentlyContinue
    }

    $finalHarnessResult = if ($script:hasErrors) { "FAIL" } else { "PASS" }
    $finalHarnessExitCode = if ($script:hasErrors) { 1 } else { 0 }
    Write-Log "CLEAN CLONE HARNESS RESULT: $finalHarnessResult"
    Write-Log "HARNESS EXIT CODE: $finalHarnessExitCode"

    $content = [System.IO.File]::ReadAllText($logPath).Replace("`r`n", "`n")
    $normalizedLines = $content.Split("`n") | ForEach-Object { $_.TrimEnd() }
    $normalizedContent = (($normalizedLines -join "`n").TrimEnd([char[]]@("`n"))) + "`n"
    $evidenceName = if ($Phase -eq "phase_2") {
        "scaffold_clean_clone_execution.txt"
    }
    else {
        "final_clean_clone_execution.txt"
    }
    $destination = Join-Path $repoRoot "evidence\$Phase\$evidenceName"
    $destinationDirectory = Split-Path $destination
    if (-not (Test-Path -LiteralPath $destinationDirectory)) {
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    }
    [System.IO.File]::WriteAllText(
        $destination,
        $normalizedContent,
        (New-Object System.Text.UTF8Encoding($false))
    )
    Write-Output "Saved normalized log to $destination"

    if ($script:hasErrors) {
        exit 1
    }

    exit 0
}
