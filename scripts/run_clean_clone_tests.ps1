$ErrorActionPreference = 'Continue'
$candidateSha = git rev-parse HEAD 2>&1 | Out-String
$candidateSha = $candidateSha.Trim()

$clonePath = Join-Path $env:TEMP ("ProofBeforePay-final-" + [guid]::NewGuid().ToString("N"))
Write-Output "Clone path: $clonePath"

$outExe = "D:\MICRO.1\evidence\phase_0\clean_clone_execution.txt"
$outAudit = "D:\MICRO.1\evidence\phase_0\clean_clone_post_test_audit.txt"

Set-Content -Path $outExe -Value "================================================================"
Add-Content -Path $outExe -Value "CLEAN CLONE EVIDENCE"
Add-Content -Path $outExe -Value "================================================================"
$timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")
Add-Content -Path $outExe -Value "Timestamp: $timestamp"
Add-Content -Path $outExe -Value "Repository URL: https://github.com/Vaibhavsahkk/Proof_Before_Pay.git"
Add-Content -Path $outExe -Value "Tested Candidate SHA: $candidateSha"
Add-Content -Path $outExe -Value "Clone Directory: $clonePath"

Add-Content -Path $outExe -Value "`n--- ENVIRONMENT PROVENANCE ---"
$gitVer = git --version 2>&1 | Out-String
Add-Content -Path $outExe -Value "Git Version:`n$gitVer"
$dockerClientVer = docker version --format 'Client: {{.Client.Version}}' 2>&1 | Out-String
$dockerServerVer = docker version --format 'Server: {{.Server.Version}}' 2>&1 | Out-String
Add-Content -Path $outExe -Value "Docker Client/Server Version:`n${dockerClientVer}${dockerServerVer}"
$composeVer = docker compose version 2>&1 | Out-String
Add-Content -Path $outExe -Value "Docker Compose Version:`n$composeVer"
$psVer = $PSVersionTable.PSVersion.ToString()
Add-Content -Path $outExe -Value "PowerShell Version:`n$psVer"
$bashVer = & 'C:\Program Files\Git\bin\bash.exe' --version 2>&1 | Select-Object -First 1
Add-Content -Path $outExe -Value "Bash Version:`n$bashVer"
$pyVer = docker run --rm python:3.12-slim python --version 2>&1 | Out-String
Add-Content -Path $outExe -Value "Container Python Version:`n$pyVer"
Add-Content -Path $outExe -Value "--------------------------------"

Add-Content -Path $outExe -Value "`nCOMMAND: git -c http.sslBackend=openssl clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath"
$cloneOutput = git -c http.sslBackend=openssl clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git $clonePath 2>&1 | Out-String
$cloneExit = $LASTEXITCODE
Add-Content -Path $outExe -Value "EXIT CODE: $cloneExit"
Add-Content -Path $outExe -Value "OUTPUT:`n$cloneOutput"

if ($cloneExit -ne 0) {
    Write-Output "Clone failed."
    exit 1
}

Set-Location $clonePath

Add-Content -Path $outExe -Value "`nCOMMAND: git checkout $candidateSha"
$checkoutOut = git checkout $candidateSha 2>&1 | Out-String
Add-Content -Path $outExe -Value "EXIT CODE: $LASTEXITCODE"
Add-Content -Path $outExe -Value "OUTPUT:`n$checkoutOut"

Add-Content -Path $outExe -Value "`nCOMMAND: git rev-parse HEAD"
$sha = git rev-parse HEAD 2>&1 | Out-String
Add-Content -Path $outExe -Value "EXIT CODE: $LASTEXITCODE"
Add-Content -Path $outExe -Value "OUTPUT:`n$sha"

Add-Content -Path $outExe -Value "`nCOMMAND: .\scripts\run_adversarial_tests.ps1"
$advOutput = .\scripts\run_adversarial_tests.ps1 *>&1 | Out-String
$advExit = $LASTEXITCODE
Add-Content -Path $outExe -Value "EXIT CODE: $advExit"
Add-Content -Path $outExe -Value "OUTPUT:`n$advOutput"

Add-Content -Path $outExe -Value "`nCOMMAND: .\verify.ps1"
$verPsOutput = .\verify.ps1 *>&1 | Out-String
$verPsExit = $LASTEXITCODE
Add-Content -Path $outExe -Value "EXIT CODE: $verPsExit"
Add-Content -Path $outExe -Value "OUTPUT:`n$verPsOutput"

Add-Content -Path $outExe -Value "`nCOMMAND: bash ./verify.sh"
$verShOutput = & 'C:\Program Files\Git\bin\bash.exe' ./verify.sh 2>&1 | Out-String
$verShExit = $LASTEXITCODE
Add-Content -Path $outExe -Value "EXIT CODE: $verShExit"
Add-Content -Path $outExe -Value "OUTPUT:`n$verShOutput"

Set-Content -Path $outAudit -Value "================================================================"
Add-Content -Path $outAudit -Value "POST-TEST AUDIT"
Add-Content -Path $outAudit -Value "================================================================"
Add-Content -Path $outAudit -Value "Timestamp: $timestamp"
Add-Content -Path $outAudit -Value "Repository URL: https://github.com/Vaibhavsahkk/Proof_Before_Pay.git"
Add-Content -Path $outAudit -Value "Tested Candidate SHA: $candidateSha"
Add-Content -Path $outAudit -Value "Clone Directory: $clonePath"

Add-Content -Path $outAudit -Value "`nCOMMAND: git diff --check (post-test dirty)"
$dirtyDiff = git diff --check 2>&1 | Out-String
Add-Content -Path $outAudit -Value "EXIT CODE: $LASTEXITCODE"
Add-Content -Path $outAudit -Value "OUTPUT:`n$dirtyDiff"

Add-Content -Path $outAudit -Value "`nCOMMAND: git status --short (post-test dirty)"
$dirtyStatus = git status --short 2>&1 | Out-String
Add-Content -Path $outAudit -Value "EXIT CODE: $LASTEXITCODE"
Add-Content -Path $outAudit -Value "OUTPUT:`n$dirtyStatus"

Add-Content -Path $outAudit -Value "`nCOMMAND: git restore evidence/phase_0/adversarial_execution.txt"
$restoreOutput = git restore evidence/phase_0/adversarial_execution.txt 2>&1 | Out-String
Add-Content -Path $outAudit -Value "EXIT CODE: $LASTEXITCODE"
Add-Content -Path $outAudit -Value "OUTPUT:`n$restoreOutput"

Add-Content -Path $outAudit -Value "`nCOMMAND: git status --short (post-test clean)"
$cleanStatus = git status --short 2>&1 | Out-String
Add-Content -Path $outAudit -Value "EXIT CODE: $LASTEXITCODE"
Add-Content -Path $outAudit -Value "OUTPUT:`n$cleanStatus"

Copy-Item "evidence\phase_0\adversarial_execution.txt" "D:\MICRO.1\evidence\phase_0\clean_clone_adversarial_execution.txt" -Force

Write-Output "Clean clone tests completed."
