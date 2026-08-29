param (
    [Parameter(Mandatory=$true)]
    [string]$CandidateSha
)

$ErrorActionPreference = 'Continue'
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path

$clonePath = Join-Path $env:TEMP ("ProofBeforePay-final-" + [guid]::NewGuid().ToString("N"))
Write-Output "Clone path: $clonePath"

$outExe = "$repoRoot\evidence\phase_0\clean_clone_execution.txt"
$outAudit = "$repoRoot\evidence\phase_0\clean_clone_post_test_audit.txt"

function Run-Command {
    param(
        [string]$CmdName,
        [scriptblock]$ScriptBlock,
        [int]$ExpectedExit = 0,
        [bool]$Fatal = $true
    )
    "`nCOMMAND: $CmdName" | Out-File -FilePath $outExe -Append -Encoding utf8
    $output = & $ScriptBlock *>&1 | Out-String
    $exitCode = $LASTEXITCODE
    "EXIT CODE: $exitCode" | Out-File -FilePath $outExe -Append -Encoding utf8
    "OUTPUT:`n$output" | Out-File -FilePath $outExe -Append -Encoding utf8

    if ($exitCode -ne $ExpectedExit) {
        Write-Output "ERROR: $CmdName expected exit $ExpectedExit but got $exitCode."
        if ($Fatal) { exit 1 }
    }
    return $output
}

try {
    "================================================================" | Out-File -FilePath $outExe -Encoding utf8
    "CLEAN CLONE EVIDENCE" | Out-File -FilePath $outExe -Append -Encoding utf8
    "================================================================" | Out-File -FilePath $outExe -Append -Encoding utf8
    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
    "Timestamp: $timestamp" | Out-File -FilePath $outExe -Append -Encoding utf8
    "Repository URL: https://github.com/Vaibhavsahkk/Proof_Before_Pay.git" | Out-File -FilePath $outExe -Append -Encoding utf8
    "Tested Candidate SHA: $CandidateSha" | Out-File -FilePath $outExe -Append -Encoding utf8
    "Clone Directory: $clonePath" | Out-File -FilePath $outExe -Append -Encoding utf8

    "`n--- ENVIRONMENT PROVENANCE ---" | Out-File -FilePath $outExe -Append -Encoding utf8
    $gitVer = git --version 2>&1 | Out-String
    "Git Version:`n$gitVer" | Out-File -FilePath $outExe -Append -Encoding utf8
    $dockerClientVer = docker version --format 'Client: {{.Client.Version}}' 2>&1 | Out-String
    $dockerServerVer = docker version --format 'Server: {{.Server.Version}}' 2>&1 | Out-String
    "Docker Client/Server Version:`n${dockerClientVer}${dockerServerVer}" | Out-File -FilePath $outExe -Append -Encoding utf8
    $composeVer = docker compose version 2>&1 | Out-String
    "Docker Compose Version:`n$composeVer" | Out-File -FilePath $outExe -Append -Encoding utf8
    $psVer = $PSVersionTable.PSVersion.ToString()
    "PowerShell Version:`n$psVer" | Out-File -FilePath $outExe -Append -Encoding utf8
    $bashVer = & 'C:\Program Files\Git\bin\bash.exe' --version 2>&1 | Select-Object -First 1
    "Bash Version:`n$bashVer" | Out-File -FilePath $outExe -Append -Encoding utf8
    $pyVer = docker run --rm python:3.12-slim python --version 2>&1 | Out-String
    "Container Python Version:`n$pyVer" | Out-File -FilePath $outExe -Append -Encoding utf8
    "--------------------------------" | Out-File -FilePath $outExe -Append -Encoding utf8

    Run-Command -CmdName "git -c http.sslBackend=openssl clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath" -ScriptBlock { git -c http.sslBackend=openssl clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath }

    Set-Location $clonePath

    Run-Command -CmdName "git checkout $CandidateSha" -ScriptBlock { git checkout $CandidateSha }

    $headOutput = Run-Command -CmdName "git rev-parse HEAD" -ScriptBlock { git rev-parse HEAD }
    $clonedHead = $headOutput.Trim()
    if ($clonedHead -ne $CandidateSha) {
        Write-Output "ERROR: Cloned HEAD ($clonedHead) does not match Candidate SHA ($CandidateSha)."
        exit 1
    }

    Run-Command -CmdName ".\scripts\run_adversarial_tests.ps1" -ScriptBlock { .\scripts\run_adversarial_tests.ps1 }
    Run-Command -CmdName ".\verify.ps1" -ScriptBlock { .\verify.ps1 }
    Run-Command -CmdName "bash ./verify.sh" -ScriptBlock { & 'C:\Program Files\Git\bin\bash.exe' ./verify.sh }

    "================================================================" | Out-File -FilePath $outAudit -Encoding utf8
    "POST-TEST AUDIT" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "================================================================" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "Timestamp: $timestamp" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "Repository URL: https://github.com/Vaibhavsahkk/Proof_Before_Pay.git" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "Tested Candidate SHA: $CandidateSha" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "Clone Directory: $clonePath" | Out-File -FilePath $outAudit -Append -Encoding utf8

    $dirtyDiffOut = git diff --check 2>&1 | Out-String
    $dirtyDiffExit = $LASTEXITCODE
    "`nCOMMAND: git diff --check (post-test dirty)" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "EXIT CODE: $dirtyDiffExit" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "OUTPUT:`n$dirtyDiffOut" | Out-File -FilePath $outAudit -Append -Encoding utf8

    $dirtyStatusOut = git status --short 2>&1 | Out-String
    $dirtyStatusExit = $LASTEXITCODE
    "`nCOMMAND: git status --short (post-test dirty)" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "EXIT CODE: $dirtyStatusExit" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "OUTPUT:`n$dirtyStatusOut" | Out-File -FilePath $outAudit -Append -Encoding utf8

    Copy-Item "evidence\phase_0\adversarial_execution.txt" "$repoRoot\evidence\phase_0\clean_clone_adversarial_execution.txt" -Force

    $restoreOut = git restore evidence/phase_0/adversarial_execution.txt 2>&1 | Out-String
    $restoreExit = $LASTEXITCODE
    "`nCOMMAND: git restore evidence/phase_0/adversarial_execution.txt" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "EXIT CODE: $restoreExit" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "OUTPUT:`n$restoreOut" | Out-File -FilePath $outAudit -Append -Encoding utf8
    if ($restoreExit -ne 0) { Write-Output "Restore failed"; exit 1 }

    $cleanStatusOut = git status --short 2>&1 | Out-String
    $cleanStatusExit = $LASTEXITCODE
    "`nCOMMAND: git status --short (post-test clean)" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "EXIT CODE: $cleanStatusExit" | Out-File -FilePath $outAudit -Append -Encoding utf8
    "OUTPUT:`n$cleanStatusOut" | Out-File -FilePath $outAudit -Append -Encoding utf8
    if ($cleanStatusExit -ne 0) { Write-Output "Status failed"; exit 1 }
    if ($cleanStatusOut.Trim() -ne "") {
        Write-Output "ERROR: Post-test clean clone is not empty: $cleanStatusOut"
        exit 1
    }

    $copiedEvidence = Get-Content "$repoRoot\evidence\phase_0\clean_clone_adversarial_execution.txt" -Raw
    if ($copiedEvidence -match "D:\\MICRO\.1") {
        Write-Output "ERROR: Copied evidence contains D:\MICRO.1"
        exit 1
    }
    if ($copiedEvidence -notmatch [regex]::Escape($clonePath)) {
        Write-Output "ERROR: Copied evidence does not contain clone path $clonePath"
        exit 1
    }
    if ($copiedEvidence -notmatch $CandidateSha) {
        Write-Output "ERROR: Copied evidence does not contain Candidate SHA $CandidateSha"
        exit 1
    }

    Write-Output "Clean clone tests completed."
} finally {
    Set-Location $repoRoot
    if (Test-Path $clonePath) {
        Remove-Item -Path $clonePath -Recurse -Force -ErrorAction SilentlyContinue
    }
}
