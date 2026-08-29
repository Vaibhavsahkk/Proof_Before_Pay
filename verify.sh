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
echo "STEP: Git Whitespace Integrity"
echo "============================================================"
git diff --check HEAD || { echo "[FAIL] Working-tree or staged diff contains whitespace errors."; exit 1; }
if [ -z "$(git status --porcelain)" ]; then
    git show --check --oneline HEAD >/dev/null || { echo "[FAIL] HEAD contains whitespace errors."; exit 1; }
else
    echo "[INFO] HEAD check deferred until the corrected working tree is committed."
fi
echo "[PASS] Git whitespace integrity checks passed."

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
CONFIG_OUT=$(OPENAI_API_KEY=SENTINEL_OPENAI_API_KEY \
    ANTHROPIC_API_KEY=SENTINEL_ANTHROPIC_API_KEY \
    GEMINI_API_KEY=SENTINEL_GEMINI_API_KEY \
    docker compose -f docker-compose.yml config)
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
if echo "$CONFIG_OUT" | grep -qE "SENTINEL_OPENAI_API_KEY|SENTINEL_ANTHROPIC_API_KEY|SENTINEL_GEMINI_API_KEY"; then
    echo "[FAIL] Found an unexpected provider credential sentinel in docker-compose.yml."
    exit 1
fi
echo "[PASS] Compose Config Isolation Check completed successfully."

echo "============================================================"
echo "STEP: Docker Build"
echo "============================================================"
docker compose -f docker-compose.yml build --no-cache
echo "[PASS] Docker Build completed successfully."

echo "============================================================"
echo "STEP: Evaluator Test Suite Execution (isolated Docker target)"
echo "============================================================"
echo "Running tests inside evaluator-only container..."
docker compose -f docker-compose.yml run --rm phase1_verifier python -m pytest -q || { echo "[FAIL] Pytest execution failed."; exit 1; }

echo "Running Phase 1 Schema Validator..."
docker compose -f docker-compose.yml run --rm phase1_verifier python scripts/validate_phase1.py || { echo "[FAIL] Phase 1 Validator failed."; exit 1; }

echo "Running Manifest Verification..."
docker compose -f docker-compose.yml run --rm phase1_verifier python scripts/verify_manifest.py || { echo "[FAIL] Manifest Verification failed."; exit 1; }

echo "[PASS] Automated Test Suite Execution completed successfully."

echo "============================================================"
echo "STEP: Smoke Execution"
echo "============================================================"
docker compose -f docker-compose.yml run --rm micro1_app
echo "[PASS] Smoke Execution completed successfully."

echo "============================================================"
echo "STEP: Recursive Container Security Assertion"
echo "============================================================"

echo "Checking required public runtime inputs and API-free baseline import..."
docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app -c \
  "test -d /app/data/cases/public && test -f /app/benchmark/RULEBOOK.md && test -f /app/benchmark/schemas/public_evidence_bundle.json && test -f /app/benchmark/schemas/output_contract.json && test -f /app/baseline/prompt_v1.txt && test -f /app/baseline/run_baseline.py && python -c 'import baseline.run_baseline'" \
  || { echo "[FAIL] Agent runtime is missing required public inputs."; exit 1; }
echo "[PASS] Required public runtime inputs are present."

IMAGE_ENVIRONMENT=$(docker image inspect micro1-challenge-phase0:latest --format '{{json .Config.Env}}') \
  || { echo "[FAIL] Runtime image inspection failed."; exit 1; }
if printf '%s\n' "$IMAGE_ENVIRONMENT" | grep -qE "OPENAI_API_KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY"; then
    echo "[FAIL] Runtime image configuration contains a provider credential name."
    exit 1
fi
echo "[PASS] Runtime image configuration contains no provider credentials."

echo "Running forced-failure isolation test..."
GROUND_TRUTH_PATH=$(cygpath -w "$(pwd)/data/cases/ground_truth" 2>/dev/null || printf '%s' "$(pwd)/data/cases/ground_truth")
set +e
FORCED_OUTPUT=$(MSYS_NO_PATHCONV=1 docker compose -f docker-compose.yml run --rm \
  --volume "${GROUND_TRUTH_PATH}:/app/data/cases/ground_truth:ro" \
  --entrypoint sh micro1_app ./scripts/verify_container_security.sh 2>&1)
FORCED_EXIT=$?
set -e
printf '%s\n' "$FORCED_OUTPUT"
echo "Forced-failure scanner exit code: $FORCED_EXIT"
if [ "$FORCED_EXIT" -ne 1 ]; then
    echo "[FAIL] Isolation check returned $FORCED_EXIT instead of the expected scanner exit 1."
    exit 1
fi
if ! printf '%s\n' "$FORCED_OUTPUT" | grep -q "data/cases/ground_truth"; then
    echo "[FAIL] Isolation check did not identify the injected ground-truth path."
    exit 1
fi
echo "[PASS] Forced-failure isolation check rejected the injected ground truth with exit 1."

# Inspect the actual verification container, not merely the image.
# We fail if any .env, .env.* (except .env.example), .git, __pycache__, .pytest_cache, .pyc, raw traces, or ground_truth are found.
docker compose -f docker-compose.yml run --rm --entrypoint sh micro1_app ./scripts/verify_container_security.sh
echo "[PASS] Recursive Container Security Assertion completed successfully."

echo "************************************************************"
echo "ALL VERIFICATION STEPS PASSED"
echo "************************************************************"
exit 0
