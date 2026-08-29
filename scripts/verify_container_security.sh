#!/bin/sh
# Container security assertion for micro1 Phase 0.
# No predictable temporary files. No suppressed find errors.
set -e

echo "Inspecting container filesystem for prohibited artifacts..."

# Run a single find command, capturing both stdout and stderr.
# SCAN_ROOT exists only to make the fail-closed behavior testable; production
# verification uses the secure default of /app.
SCAN_ROOT=${SCAN_ROOT:-/app}
set +e
OUTPUT=$(find "$SCAN_ROOT" \( \
    -name ".git" -o \
    -name ".env" -o \
    \( -name ".env.*" ! -name ".env.example" \) -o \
    -name "__pycache__" -o \
    -name "*.pyc" -o \
    -name ".pytest_cache" -o \
    -path "*/traces/raw" -o \
    -path "*/traces/raw/*" -o \
    -path "*/trajectories/raw" -o \
    -path "*/trajectories/raw/*" -o \
    -path "*/data/cases/ground_truth" -o \
    -path "*/data/cases/ground_truth/*" -o \
    -name "ground_truth.json" \
\) -print 2>&1)
FIND_EXIT=$?
set -e

if [ "$FIND_EXIT" -ne 0 ]; then
    printf "[FAIL] Container filesystem scan failed.\n"
    printf "%s\n" "$OUTPUT"
    exit 1
fi

if [ -n "$OUTPUT" ]; then
    printf "[FAIL] Found prohibited secret or artifact:\n"
    printf "%s\n" "$OUTPUT"
    exit 1
fi

UID_VAL=$(id -u)
if [ "$UID_VAL" -eq 0 ]; then
    printf "[FAIL] Container is running as root (UID 0).\n"
    exit 1
fi

printf "[PASS] Container security assertion passed. No prohibited artifacts found.\n"
