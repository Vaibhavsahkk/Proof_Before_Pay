#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-}"
if [[ -z "$PHASE" ]]; then
  echo "Usage: ./scripts/PHASE_GATE.sh <phase-number>"
  exit 2
fi

STATUS_FILE="STATUS.md"
APPROVAL_FILE="reports/phase_${PHASE}_approval.txt"

[[ -f "$STATUS_FILE" ]] || { echo "STATUS.md missing"; exit 1; }
[[ -f "$APPROVAL_FILE" ]] || { echo "External approval evidence missing: $APPROVAL_FILE"; exit 1; }

grep -Fxq 'PHASE APPROVED — 100%' "$APPROVAL_FILE" || { echo "Exact external approval phrase not found."; exit 1; }

echo "External approval evidence found for Phase $PHASE."
echo "Human/ChatGPT must still verify that the approval corresponds to the current commit/state."
