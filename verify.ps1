$ErrorActionPreference = "Stop"

Write-Host "Starting Micro1 Challenge Verification Pipeline (PowerShell)..."

# 1. Dependency Check
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "[FAIL] Docker is not installed or not in PATH."
    exit 1
}
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Error "[FAIL] Git is not installed or not in PATH."
    exit 1
}

Write-Host "============================================================"
Write-Host "STEP: Git Tracked Traces Check"
Write-Host "============================================================"
$trackedTraces = git ls-files "traces/"
$invalidTraces = $trackedTraces | Where-Object { -not $_.StartsWith("traces/sanitized/") }
if ($invalidTraces) {
    Write-Error "[FAIL] Found improperly tracked traces:`n$invalidTraces"
    exit 1
}
Write-Host "[PASS] Git Tracked Traces Check completed successfully."

Write-Host "============================================================"
Write-Host "STEP: Compose Config Isolation Check"
Write-Host "============================================================"
$configOut = docker compose -f docker-compose.yml config | Out-String
if ($configOut -match "/app/src" -or $configOut -match "type: bind") {
    Write-Error "[FAIL] Found unexpected bind mounts in docker-compose.yml."
    exit 1
}
Write-Host "[PASS] Compose Config Isolation Check completed successfully."

Write-Host "============================================================"
Write-Host "STEP: Docker Build"
Write-Host "============================================================"
docker compose -f docker-compose.yml build --no-cache
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[PASS] Docker Build completed successfully."

Write-Host "============================================================"
Write-Host "STEP: Automated Test Suite Execution (Docker-driven)"
Write-Host "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app sh -c "pip install --user -r requirements-dev.txt && python -m pytest -q"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[PASS] Automated Test Suite Execution completed successfully."

Write-Host "============================================================"
Write-Host "STEP: Smoke Execution"
Write-Host "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[PASS] Smoke Execution completed successfully."

Write-Host "============================================================"
Write-Host "STEP: Recursive Container Security Assertion"
Write-Host "============================================================"
$script = @'
    FAILED=0
    echo "Inspecting container filesystem for prohibited artifacts..."
    for f in $(find /app -type f -o -type d); do
        case "$f" in
            */.git|*/.git/*) echo "[FAIL] Found .git repository artifact: $f"; FAILED=1 ;;
            */.env|*/.env.local|*/.env.production|*/.env.development|*/.env.test) echo "[FAIL] Found prohibited secret file: $f"; FAILED=1 ;;
            */__pycache__|*/__pycache__/*|*.pyc) echo "[FAIL] Found python cache artifact: $f"; FAILED=1 ;;
            */.pytest_cache|*/.pytest_cache/*) echo "[FAIL] Found pytest cache artifact: $f"; FAILED=1 ;;
            */traces/raw|*/traces/raw/*) echo "[FAIL] Found raw trace artifact: $f"; FAILED=1 ;;
        esac
    done
    UID=$(id -u)
    if [ "$UID" -eq 0 ]; then
        echo "[FAIL] Container is running as root (UID 0)."
        FAILED=1
    fi
    if [ $FAILED -ne 0 ]; then exit 1; fi
    echo "[PASS] Container security assertion passed. No prohibited artifacts found."
'@

docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app -c $script
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "[PASS] Recursive Container Security Assertion completed successfully."

Write-Host "************************************************************"
Write-Host "ALL VERIFICATION STEPS PASSED"
Write-Host "************************************************************"
