# Phase 1 Review Packet

## Acceptance Criterion Matrix
| Criterion | Status | Evidence/File |
| --------- | ------ | ------------- |
| Precise scope document | PASS | `docs/PHASE_1_SCOPE.md` |
| Versioned hardened schemas | PASS | `benchmark/schemas/*.json` |
| Strict Ground-truth rulebook | PASS | `benchmark/RULEBOOK.md` |
| Five synthetic cases | PASS | `data/cases/public/` and `data/cases/ground_truth/` |
| Leakage-safe structure | PASS | `scripts/validate_phase1.py` and `tests/test_phase1_validation.py` |
| Oracle / Deterministic validation | PASS | `scripts/validate_phase1.py` (Full derived matrix and findings list) |
| Manifest verification | PASS | `scripts/verify_manifest.py` and `tests/test_manifest.py` |
| Evaluation design | PASS | `eval/EVAL_DESIGN.md` |
| Evidence & governance | PASS | This document and `evidence/phase_1/final_clean_clone_execution.txt` |

## Assumptions
- No Phase 2+ implementations are expected (baseline, agent, etc. remain empty).
- The evaluation will rely purely on exact metric matching of the JSON fields.
- Decimal strings are used exclusively for all money values to ensure accurate deterministic verification.

## Risks
- The LLM agent in Phase 2 may hallucinate values beyond the schema limits; the evaluation suite must handle invalid schemas gracefully.
- The strict decimal constraints require the agent to correctly format numbers with exact 2 decimal places.

## Blockers
- None.

## Reproduction Steps
1. Run `python scripts/validate_phase1.py`
2. Run `pytest tests/test_phase1_validation.py`
3. Run `pytest tests/test_manifest.py`
4. Run POSIX/Windows core verification (`./verify.sh` and `.\verify.ps1`)
5. Verify `evidence/phase_1` matches generated checksums.

## Exact Changed Files
See `git ls-files` and `git diff` output in the final clean clone execution log.
