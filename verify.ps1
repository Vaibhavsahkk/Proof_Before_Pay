$ErrorActionPreference = "Continue"

Write-Output "Starting Micro1 Challenge Verification Pipeline (PowerShell)..."

# 1. Dependency Check
if (-not (Get-Command "docker")) {
    Write-Error "[FAIL] Docker is not installed or not in PATH."
    exit 1
}
if (-not (Get-Command "git")) {
    Write-Error "[FAIL] Git is not installed or not in PATH."
    exit 1
}

Write-Output "============================================================"
Write-Output "STEP: Git Whitespace Integrity"
Write-Output "============================================================"
$workingTreeCheck = git diff --check HEAD 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Output $workingTreeCheck.TrimEnd()
    Write-Error "[FAIL] Working-tree or staged diff contains whitespace errors."
    exit 1
}
$treeState = git status --porcelain
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Git status failed."
    exit $LASTEXITCODE
}
if (-not $treeState) {
    $committedCheck = git show --check --oneline HEAD 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Output $committedCheck.TrimEnd()
        Write-Error "[FAIL] HEAD contains whitespace errors."
        exit 1
    }
}
else {
    Write-Output "[INFO] HEAD check deferred until the corrected working tree is committed."
}
Write-Output "[PASS] Git whitespace integrity checks passed."

Write-Output "============================================================"
Write-Output "STEP: Git Tracked Traces Check"
Write-Output "============================================================"
$trackedTraces = git ls-files "traces/"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Git command failed."
    exit $LASTEXITCODE
}
$invalidTraces = $trackedTraces | Where-Object {
    -not [string]::IsNullOrWhiteSpace($_) -and
    -not $_.StartsWith("traces/sanitized/") -and
    $_ -ne "traces/README.md"
}
if ($invalidTraces) {
    Write-Error "[FAIL] Found improperly tracked traces:`n$invalidTraces"
    exit 1
}
$trackedTrajectories = git ls-files "trajectories/"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Git command failed."
    exit $LASTEXITCODE
}
$invalidTrajectories = $trackedTrajectories | Where-Object {
    -not [string]::IsNullOrWhiteSpace($_) -and
    -not $_.StartsWith("trajectories/sanitized/") -and
    $_ -ne "trajectories/README.md"
}
if ($invalidTrajectories) {
    Write-Error "[FAIL] Found improperly tracked trajectories:`n$invalidTrajectories"
    exit 1
}
Write-Output "[PASS] Git Tracked Traces Check completed successfully."

Write-Output "============================================================"
Write-Output "STEP: Compose Config Isolation Check"
Write-Output "============================================================"
$credentialNames = @("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")
$savedCredentials = @{}
foreach ($name in $credentialNames) {
    $savedCredentials[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
    [Environment]::SetEnvironmentVariable($name, "SENTINEL_$name", "Process")
}
try {
    $configOut = docker compose -f docker-compose.yml config | Out-String
    $configExit = $LASTEXITCODE
}
finally {
    foreach ($name in $credentialNames) {
        [Environment]::SetEnvironmentVariable($name, $savedCredentials[$name], "Process")
    }
}
if ($configExit -ne 0) {
    Write-Error "[FAIL] Docker compose config failed."
    exit $configExit
}
if ($configOut -match "/app/src" -or $configOut -match "type: bind") {
    Write-Error "[FAIL] Found unexpected bind mounts in docker-compose.yml."
    exit 1
}
foreach ($name in $credentialNames) {
    if ($configOut -match [regex]::Escape($name) -or $configOut -match [regex]::Escape("SENTINEL_$name")) {
        Write-Error "[FAIL] Found unexpected provider credential forwarding in docker-compose.yml."
        exit 1
    }
}
Write-Output "[PASS] Compose Config Isolation Check completed successfully."

Write-Output "============================================================"
Write-Output "STEP: Docker Build"
Write-Output "============================================================"
docker compose -f docker-compose.yml build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Docker Build failed."
    exit $LASTEXITCODE
}
Write-Output "[PASS] Docker Build completed successfully."

Write-Output "============================================================"
Write-Output "STEP: Evaluator Test Suite Execution (isolated Docker target)"
Write-Output "============================================================"
Write-Output "Running tests inside evaluator-only container..."
docker compose -f docker-compose.yml run --rm phase1_verifier python -m pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Pytest execution failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Output "Running Phase 1 Schema Validator..."
docker compose -f docker-compose.yml run --rm phase1_verifier python scripts/validate_phase1.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Phase 1 Validator failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Output "Running Manifest Verification..."
docker compose -f docker-compose.yml run --rm phase1_verifier python scripts/verify_manifest.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Manifest Verification failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Output "[PASS] Automated Test Suite Execution completed successfully."

Write-Output "============================================================"
Write-Output "STEP: Smoke Execution"
Write-Output "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Smoke execution failed."
    exit $LASTEXITCODE
}
Write-Output "[PASS] Smoke Execution completed successfully."

Write-Output "============================================================"
Write-Output "STEP: Recursive Container Security Assertion"
Write-Output "============================================================"

Write-Output "Checking required public runtime inputs and API-free baseline import..."
docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app -c "test -d /app/data/cases/public && test -f /app/benchmark/RULEBOOK.md && test -f /app/benchmark/schemas/public_evidence_bundle.json && test -f /app/benchmark/schemas/output_contract.json && test -f /app/baseline/prompt_v1.txt && test -f /app/baseline/run_baseline.py && python -c 'import baseline.run_baseline'"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Agent runtime is missing required public inputs."
    exit $LASTEXITCODE
}
Write-Output "[PASS] Required public runtime inputs are present."

$imageEnvironment = docker image inspect micro1-challenge-phase0:latest --format '{{json .Config.Env}}' | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Runtime image inspection failed."
    exit $LASTEXITCODE
}
foreach ($name in $credentialNames) {
    if ($imageEnvironment -match [regex]::Escape($name)) {
        Write-Error "[FAIL] Runtime image configuration contains a provider credential name."
        exit 1
    }
}
Write-Output "[PASS] Runtime image configuration contains no provider credentials."

Write-Output "Running forced-failure isolation test..."
$groundTruthPath = (Resolve-Path "data/cases/ground_truth").Path
$forcedOutput = docker compose -f docker-compose.yml run --rm --volume "${groundTruthPath}:/app/data/cases/ground_truth:ro" --entrypoint sh micro1_app ./scripts/verify_container_security.sh 2>&1 | Out-String
$forcedExit = $LASTEXITCODE
Write-Output $forcedOutput.TrimEnd()
Write-Output "Forced-failure scanner exit code: $forcedExit"
if ($forcedExit -ne 1) {
    Write-Error "[FAIL] Isolation check returned $forcedExit instead of the expected scanner exit 1."
    exit 1
}
if ($forcedOutput -notmatch "data/cases/ground_truth") {
    Write-Error "[FAIL] Isolation check did not identify the injected ground-truth path."
    exit 1
}
Write-Output "[PASS] Forced-failure isolation check rejected the injected ground truth with exit 1."

docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app ./scripts/verify_container_security.sh
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Security assertion failed."
    exit $LASTEXITCODE
}
Write-Output "[PASS] Recursive Container Security Assertion completed successfully."

Write-Output "************************************************************"
Write-Output "ALL VERIFICATION STEPS PASSED"
Write-Output "************************************************************"
exit 0
