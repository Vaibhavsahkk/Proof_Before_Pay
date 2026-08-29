param (
    [Parameter(Mandatory=$true)]
    [string]$CandidateSha
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$evidenceDir = "$repoRoot\evidence\phase_0"
$outProof = "$evidenceDir\FINAL_PHASE0_PROOF.txt"

$timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")

function Normalize-Content {
    param([string]$path)
    if (-not (Test-Path $path)) {
        Write-Error "File not found: $path"
        exit 1
    }
    $content = Get-Content -Path $path -Raw
    # Normalize line endings to LF, remove trailing whitespace
    $content = $content -replace "`r`n", "`n"
    $content = $content -replace "[ \t]+`n", "`n"
    # Remove trailing blank lines
    $content = $content.TrimEnd("`n")
    # Add exactly one final newline
    return $content + "`n"
}

# Verify container security exit code
$ErrorActionPreference = 'Continue'
$securityOutput = docker compose -f "$repoRoot\docker-compose.yml" run --rm --entrypoint sh micro1_app ./scripts/verify_container_security.sh 2>&1 | Out-String
$ErrorActionPreference = 'Stop'
$securityExit = $LASTEXITCODE
if ($securityExit -ne 0) {
    Write-Error "Container security check failed with exit code $securityExit"
    exit 1
}

$exeContent = Normalize-Content "$evidenceDir\clean_clone_execution.txt"
$advContent = Normalize-Content "$evidenceDir\clean_clone_adversarial_execution.txt"
$auditContent = Normalize-Content "$evidenceDir\clean_clone_post_test_audit.txt"

Set-Content -Path "$evidenceDir\clean_clone_execution.txt" -Value $exeContent -NoNewline -Encoding utf8
Set-Content -Path "$evidenceDir\clean_clone_adversarial_execution.txt" -Value $advContent -NoNewline -Encoding utf8
Set-Content -Path "$evidenceDir\clean_clone_post_test_audit.txt" -Value $auditContent -NoNewline -Encoding utf8

$proofContent = "================================================================`n" +
"PHASE 0 FINAL AUDIT PROOF`n" +
"================================================================`n" +
"STATUS: READY FOR EXTERNAL CHATGPT REVIEW`n" +
"TIMESTAMP: $timestamp`n" +
"REPOSITORY: https://github.com/Vaibhavsahkk/Proof_Before_Pay.git`n" +
"CANDIDATE SHA: $CandidateSha`n" +
"NOTE: Appended evidence text has line endings and trailing whitespace normalized for Git hygiene.`n" +
"`n================================================================`n" +
"1. CLEAN CLONE REPRODUCTION EVIDENCE`n" +
"================================================================`n" +
$exeContent +
"`n================================================================`n" +
"2. CLEAN CLONE ADVERSARIAL EXECUTION EVIDENCE`n" +
"================================================================`n" +
$advContent +
"`n================================================================`n" +
"3. POST-TEST AUDIT (CLEANLINESS VERIFICATION)`n" +
"================================================================`n" +
$auditContent +
"`n================================================================`n" +
"4. CONTAINER SECURITY VERIFICATION`n" +
"================================================================`n" +
$securityOutput.TrimEnd("`r","`n"," ") + "`n"

$proofContent = $proofContent -replace "`r`n", "`n"
$proofContent = $proofContent -replace "[ \t]+`n", "`n"
Set-Content -Path $outProof -Value $proofContent -NoNewline -Encoding utf8

Write-Output "Final proof generated at $outProof"
