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
$configOut = docker compose -f docker-compose.yml config | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Docker compose config failed."
    exit $LASTEXITCODE
}
if ($configOut -match "/app/src" -or $configOut -match "type: bind") {
    Write-Error "[FAIL] Found unexpected bind mounts in docker-compose.yml."
    exit 1
}
if ($configOut -match "OPENAI_API_KEY" -or $configOut -match "ANTHROPIC_API_KEY" -or $configOut -match "GEMINI_API_KEY") {
    Write-Error "[FAIL] Found unexpected API key credentials forwarded in docker-compose.yml."
    exit 1
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
Write-Output "STEP: Automated Test Suite Execution (Docker-driven)"
Write-Output "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app sh -c "pip install --user -r requirements-dev.txt && python -m pytest -q"
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Tests failed."
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
