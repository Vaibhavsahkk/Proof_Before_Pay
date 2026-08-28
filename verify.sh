#!/usr/bin/env bash
set -e
set -o pipefail

echo "Starting Micro1 Challenge Verification Pipeline (POSIX)..."

# 1. Dependency Check
if ! command -v docker; then
    echo "[FAIL] Docker is not installed or not in PATH."
    exit 1
fi
if ! command -v git; then
    echo "[FAIL] Git is not installed or not in PATH."
    exit 1
fi

echo "============================================================"
echo "STEP: Git Tracked Traces Check"
echo "============================================================"
# Enforce trace allowlisting: Fail if any trace outside traces/sanitized/** is tracked.
if ! TRACKED_TRACES=$(git ls-files -- "traces/"); then
    echo "[FAIL] Git command failed while listing traces."
    exit 1
fi
INVALID_TRACES=()
while IFS= read -r tracked_path; do
    [ -z "$tracked_path" ] && continue
    case "$tracked_path" in
        traces/sanitized/*|traces/README.md) ;;
        *) INVALID_TRACES+=("$tracked_path") ;;
    esac
done <<< "$TRACKED_TRACES"
if [ "${#INVALID_TRACES[@]}" -ne 0 ]; then
    echo "[FAIL] Found improperly tracked traces:"
    printf '%s\n' "${INVALID_TRACES[@]}"
    exit 1
fi
if ! TRACKED_TRAJECTORIES=$(git ls-files -- "trajectories/"); then
    echo "[FAIL] Git command failed while listing trajectories."
    exit 1
fi
INVALID_TRAJECTORIES=()
while IFS= read -r tracked_path; do
    [ -z "$tracked_path" ] && continue
    case "$tracked_path" in
        trajectories/sanitized/*|trajectories/README.md) ;;
        *) INVALID_TRAJECTORIES+=("$tracked_path") ;;
    esac
done <<< "$TRACKED_TRAJECTORIES"
if [ "${#INVALID_TRAJECTORIES[@]}" -ne 0 ]; then
    echo "[FAIL] Found improperly tracked trajectories:"
    printf '%s\n' "${INVALID_TRAJECTORIES[@]}"
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
if echo "$CONFIG_OUT" | grep -qE "OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY"; then
    echo "[FAIL] Found unexpected API key credentials forwarded in docker-compose.yml."
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
docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app ./scripts/verify_container_security.sh
echo "[PASS] Recursive Container Security Assertion completed successfully."

echo "************************************************************"
echo "ALL VERIFICATION STEPS PASSED"
echo "************************************************************"
exit 0
