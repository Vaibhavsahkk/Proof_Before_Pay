$ErrorActionPreference = "Continue"

$candidateSha = "9185348dd135962870295365d421abff41294d89"
$cloneDir = "Phase1TestClone-" + [guid]::NewGuid().ToString("N")
$clonePath = Join-Path $env:TEMP $cloneDir
$logPath = Join-Path $env:TEMP "clean_clone_log_$cloneDir.txt"

Function Log {
    param([string]$message)
    Write-Output $message
    $message | Out-File -FilePath $logPath -Append -Encoding utf8
}

Function RunAndLog {
    param([string]$name, [scriptblock]$command)
    Log "========================================"
    Log "COMMAND: $name"
    Log "========================================"
    
    try {
        $output = & $command 2>&1
        foreach ($line in $output) {
            Log $line.ToString()
        }
        $exitCode = $LASTEXITCODE
        Log "EXIT CODE: $exitCode"
    } catch {
        Log "Exception: $_"
        $exitCode = 1
        Log "EXIT CODE: 1"
    }
    Log ""
}

Log "--- PHASE 1 FINAL CLEAN CLONE EXECUTION ---"
Log "CANDIDATE SHA: $candidateSha"

RunAndLog "git clone" { git clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath }

Set-Location $clonePath

RunAndLog "git checkout" { git checkout $candidateSha }

RunAndLog "python scripts/validate_phase1.py" { python scripts/validate_phase1.py }

RunAndLog "python scripts/verify_manifest.py" { python scripts/verify_manifest.py }

RunAndLog "pytest tests/test_phase1_validation.py tests/test_manifest.py" { pytest tests/test_phase1_validation.py tests/test_manifest.py }

RunAndLog ".\verify.ps1" { .\verify.ps1 }

RunAndLog "bash ./verify.sh" { & 'C:\Program Files\Git\bin\bash.exe' ./verify.sh }

RunAndLog "git diff --check" { git diff --check }

RunAndLog "git diff --cached --check" { git diff --cached --check }

RunAndLog "git status --short" { git status --short }

Set-Location "d:\MICRO.1"
Write-Output "Log written to $logPath"
Copy-Item $logPath "d:\MICRO.1\evidence\phase_1\final_clean_clone_execution.txt" -Force

# Normalize line endings to LF before committing, without using -replace which might mess encoding up.
# Actually, git will handle CRLF->LF if core.autocrlf is true, but let's just make sure.
$content = [System.IO.File]::ReadAllText("d:\MICRO.1\evidence\phase_1\final_clean_clone_execution.txt")
$content = $content.Replace("`r`n", "`n")
[System.IO.File]::WriteAllText("d:\MICRO.1\evidence\phase_1\final_clean_clone_execution.txt", $content, (New-Object System.Text.UTF8Encoding($false)))
