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

# Audit the exact candidate tree for Phase 1 contamination. Planning documents may
# describe later phases, but the candidate must not contain active implementation.
$phaseScopeCommand = "git ls-tree -r --name-only $CandidateSha -- agent baseline benchmark data eval"
$phaseScopeLines = & git ls-tree -r --name-only $CandidateSha -- agent baseline benchmark data eval 2>&1
$phaseScopeExit = $LASTEXITCODE
$phaseScopeOutput = $phaseScopeLines | Out-String
if ($phaseScopeExit -ne 0) {
    Write-Error "Phase-boundary tree inspection failed with exit code $phaseScopeExit"
    exit 1
}

$expectedPhaseScopeFiles = @(
    "agent/README.md",
    "baseline/README.md",
    "benchmark/README.md",
    "data/README.md",
    "eval/README.md"
)
$actualPhaseScopeFiles = @($phaseScopeLines | ForEach-Object { $_.ToString().Trim() } | Where-Object { $_ })
$phaseScopeDifference = Compare-Object -ReferenceObject $expectedPhaseScopeFiles -DifferenceObject $actualPhaseScopeFiles
if ($phaseScopeDifference) {
    Write-Error "Phase 1 implementation directory contents differ from the approved Phase 0 placeholder allowlist"
    exit 1
}

$candidateTreeCommand = "git ls-tree -r --name-only $CandidateSha"
$candidateTreeLines = & git ls-tree -r --name-only $CandidateSha 2>&1
$candidateTreeExit = $LASTEXITCODE
if ($candidateTreeExit -ne 0) {
    Write-Error "Candidate tree inspection failed with exit code $candidateTreeExit"
    exit 1
}

$codeExtensions = @(".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".cs", ".c", ".cc", ".cpp", ".h", ".hpp", ".rb", ".php", ".sql", ".ipynb")
$candidateCodeFiles = @(
    $candidateTreeLines |
        ForEach-Object { $_.ToString().Trim() } |
        Where-Object { $_ -and ($codeExtensions -contains [System.IO.Path]::GetExtension($_).ToLowerInvariant()) }
)
$expectedPhase0CodeFiles = @(
    "src/main.py",
    "src/utils/human_checkpoint.py",
    "src/utils/logger.py",
    "tests/test_environment.py",
    "tests/test_human_checkpoint.py",
    "tests/test_logger.py"
)
$codeFileDifference = Compare-Object -ReferenceObject $expectedPhase0CodeFiles -DifferenceObject $candidateCodeFiles
if ($codeFileDifference) {
    Write-Error "Candidate contains an unapproved executable/code file or is missing an approved Phase 0 code file"
    exit 1
}
$candidateCodeOutput = ($candidateCodeFiles -join "`n") + "`n"

$forbiddenPattern = '(invoice|supplier|vendor|purchase[ _-]?order|goods[ _-]?receipt|\bgrn\b|fraud|bank[ _-]?detail|duplicate[ _-]?bill|ground[ _-]?truth|benchmark[ _-]?case|payment[ _-]?execution)'
$phaseContentCommand = "git grep -n -I -E `"$forbiddenPattern`" $CandidateSha -- src/main.py src/utils/human_checkpoint.py src/utils/logger.py"
$phaseContentLines = & git grep -n -I -E $forbiddenPattern $CandidateSha -- src/main.py src/utils/human_checkpoint.py src/utils/logger.py 2>&1
$phaseContentExit = $LASTEXITCODE
$phaseContentOutput = $phaseContentLines | Out-String
if ($phaseContentExit -eq 0) {
    Write-Error "Candidate contains active project-domain terms in implementation scope: $phaseContentOutput"
    exit 1
}
if ($phaseContentExit -ne 1) {
    Write-Error "Phase-boundary content search failed with exit code $phaseContentExit"
    exit 1
}

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
if ($exeContent -notmatch [regex]::Escape("Tested Candidate SHA: $CandidateSha") -or $auditContent -notmatch [regex]::Escape("Tested Candidate SHA: $CandidateSha")) {
    Write-Error "Candidate SHA mismatch in execution or audit evidence file"
    exit 1
}
if ($advContent -notmatch $CandidateSha) {
    Write-Error "Candidate SHA mismatch in adversarial evidence file"
    exit 1
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
    if ($matched.Trim() -ne "" -and $matched.Trim() -ne "POST-TEST AUDIT RESULT: PASS") {
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
$securityOutput.TrimEnd("`r","`n"," ") +
"`n`n================================================================`n" +
"5. PHASE 1 CONTAMINATION AUDIT`n" +
"================================================================`n" +
"TESTED SOURCE SHA: $CandidateSha`n" +
"COMMAND: $phaseScopeCommand`n" +
"EXIT CODE: $phaseScopeExit`n" +
"OUTPUT:`n$phaseScopeOutput" +
"ASSERTION: Only approved Phase 0 placeholder README files are present in agent/baseline/benchmark/data/eval.`n" +
"RESULT: PASS`n`n" +
"COMMAND: $candidateTreeCommand | filter executable/code extensions`n" +
"EXIT CODE: $candidateTreeExit`n" +
"OUTPUT:`n$candidateCodeOutput" +
"ASSERTION: The candidate contains only the approved Phase 0 scaffold and utility test code files.`n" +
"RESULT: PASS`n`n" +
"COMMAND: $phaseContentCommand`n" +
"EXIT CODE: $phaseContentExit (expected: 1 means no matches)`n" +
"OUTPUT:`n$phaseContentOutput" +
"ASSERTION: No active AP/invoice/supplier/fraud/benchmark/ground-truth/payment-execution domain logic was found in the candidate implementation scope.`n" +
"PHASE 1 CONTAMINATION AUDIT RESULT: PASS`n"

$proofContent = $proofContent -replace "`r`n", "`n"
$proofContent = $proofContent -replace "[ \t]+`n", "`n"
Set-Content -Path $outProof -Value $proofContent -NoNewline -Encoding utf8

Write-Output "Final proof generated at $outProof"
