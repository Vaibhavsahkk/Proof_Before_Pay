param (
    [Parameter(Mandatory=$true)]
    [string]$CandidateSha
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$evidenceDir = "$repoRoot\evidence\phase_0"
$outProof = "$evidenceDir\FINAL_PHASE0_PROOF.txt"

if ($CandidateSha.Length -ne 40 -or $CandidateSha -match "[^a-f0-9]") {
    Write-Error "Invalid CandidateSha"
    exit 1
}

$commitType = git cat-file -t $CandidateSha 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $commitType.Trim() -ne "commit") {
    Write-Error "Candidate SHA does not exist"
    exit 1
}

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

# Validations
$evidenceFiles = @($exeContent, $advContent, $auditContent)
foreach ($file in $evidenceFiles) {
    if ($file -notmatch [regex]::Escape("Tested Candidate SHA: $CandidateSha")) {
        Write-Error "Candidate SHA mismatch in evidence file"
        exit 1
    }
}

if ($exeContent -notmatch "Note: switching to '$CandidateSha'") {
    Write-Error "Recorded clean-clone HEAD does not match CandidateSha"
    exit 1
}

if ($advContent -match [regex]::Escape("D:\MICRO.1")) {
    Write-Error "Adversarial evidence ran in main repo"
    exit 1
}

if (-not ($exeContent -match "CLEAN CLONE HARNESS RESULT: PASS")) { Write-Error "exeContent missing PASS marker"; exit 1 }
if (-not ($auditContent -match "POST-TEST AUDIT RESULT: PASS")) { Write-Error "auditContent missing PASS marker"; exit 1 }
if (-not ($advContent -match "HARNESS EXIT: 0")) { Write-Error "advContent missing PASS marker"; exit 1 }

if ($exeContent -match "COMMAND: \.\\verify\.ps1[\r\n]+EXIT CODE: ([1-9][0-9]*)") { Write-Error "verify.ps1 exited non-zero"; exit 1 }
if ($exeContent -match "COMMAND: bash \./verify\.sh[\r\n]+EXIT CODE: ([1-9][0-9]*)") { Write-Error "verify.sh exited non-zero"; exit 1 }

if ($auditContent -match "COMMAND: git status --short \(post-test clean\)[\r\n]+EXIT CODE: [0-9]+[\r\n]+OUTPUT:[\r\n]+([^\r\n]+)") {
    $matched = $matches[1]
    if ($matched.Trim() -ne "") {
        Write-Error "post-test final status is not empty"
        exit 1
    }
}

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
