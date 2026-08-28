#!/usr/bin/env bash
set -e
set -o pipefail

echo "Starting Micro1 Challenge Verification Pipeline (POSIX)..."

# 1. Dependency Check
if ! command -v docker >/dev/null 2>&1; then
    echo "[FAIL] Docker is not installed or not in PATH."
    exit 1
fi
if ! command -v git >/dev/null 2>&1; then
    echo "[FAIL] Git is not installed or not in PATH."
    exit 1
fi

echo "============================================================"
echo "STEP: Git Tracked Traces Check"
echo "============================================================"
# Enforce trace allowlisting: Fail if any trace outside traces/sanitized/** is tracked.
INVALID_TRACES=$(git ls-files "traces/" | grep -v "^traces/sanitized/" || true)
if [ -n "$INVALID_TRACES" ]; then
    echo "[FAIL] Found improperly tracked traces:"
    echo "$INVALID_TRACES"
    exit 1
fi
echo "[PASS] Git Tracked Traces Check completed successfully."

echo "============================================================"
echo "STEP: Compose Config Isolation Check"
echo "============================================================"
CONFIG_OUT=$(docker compose -f docker-compose.yml config)
if echo "$CONFIG_OUT" | grep -q "/app/src"; then
    echo "[FAIL] Found unexpected bind mounts in docker-compose.yml."
    exit 1
fi
if echo "$CONFIG_OUT" | grep -q "type: bind"; then
    echo "[FAIL] Found unexpected bind mounts in docker-compose.yml."
    exit 1
fi
echo "[PASS] Compose Config Isolation Check completed successfully."

echo "============================================================"
echo "STEP: Docker Build"
echo "============================================================"
docker compose -f docker-compose.yml build --no-cache
echo "[PASS] Docker Build completed successfully."

echo "============================================================"
echo "STEP: Automated Test Suite Execution (Docker-driven)"
echo "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app sh -c "pip install --user -r requirements-dev.txt && python -m pytest -q"
echo "[PASS] Automated Test Suite Execution completed successfully."

echo "============================================================"
echo "STEP: Smoke Execution"
echo "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app
echo "[PASS] Smoke Execution completed successfully."

echo "============================================================"
echo "STEP: Recursive Container Security Assertion"
echo "============================================================"
# Inspect the actual verification container, not merely the image.
# We fail if any .env, .env.* (except .env.example), .git, __pycache__, .pytest_cache, .pyc, or raw traces are found.
docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app -c '
    FAILED=0
    echo "Inspecting container filesystem for prohibited artifacts..."
    
    # Check for forbidden files
    for f in $(find /app -type f -o -type d); do
        case "$f" in
            */.git|*/.git/*)
                echo "[FAIL] Found .git repository artifact: $f"
                FAILED=1
                ;;
            */.env|*/.env.local|*/.env.production|*/.env.development|*/.env.test)
                echo "[FAIL] Found prohibited secret file: $f"
                FAILED=1
                ;;
            */__pycache__|*/__pycache__/*|*.pyc)
                echo "[FAIL] Found python cache artifact: $f"
                FAILED=1
                ;;
            */.pytest_cache|*/.pytest_cache/*)
                echo "[FAIL] Found pytest cache artifact: $f"
                FAILED=1
                ;;
            */traces/raw|*/traces/raw/*)
                echo "[FAIL] Found raw trace artifact: $f"
                FAILED=1
                ;;
        esac
    done
    
    # Check for non-root user
    UID=$(id -u)
    if [ "$UID" -eq 0 ]; then
        echo "[FAIL] Container is running as root (UID 0)."
        FAILED=1
    fi
    
    if [ $FAILED -ne 0 ]; then
        exit 1
    fi
    echo "[PASS] Container security assertion passed. No prohibited artifacts found."
'
echo "[PASS] Recursive Container Security Assertion completed successfully."

echo "************************************************************"
echo "ALL VERIFICATION STEPS PASSED"
echo "************************************************************"
