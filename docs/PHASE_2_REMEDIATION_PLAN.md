# Phase 2 Remediation Plan

## Context
During the external review of Phase 2 (Fair Baseline), the benchmark received a `PHASE FAIL` verdict because the baseline agent achieved exactly 100% Exact Case-Level Recommendation Accuracy on the existing 6-case frozen benchmark. 

The external reviewer ruled this a blocker: 100% baseline accuracy leaves zero measurable headroom for demonstrating agentic improvement (which is the primary metric and a mandatory scorecard item for the hackathon). To prove the value of an agentic workflow over a zero-shot prompt, the baseline must fail on at least some cases.

## Objectives
1. **Expand the Benchmark:** Increase the total number of test cases from 6 to 10 by adding 4 new cases that represent realistic, challenging edge cases where zero-shot baseline performance is expected to struggle (e.g., nuanced policy application, conflicting signals across multiple documents, or reasoning heavily dependent on prior context).
2. **Preserve Immutability:** Existing artifacts must remain exactly as they are. The first 6 cases, their ground truth, the previous manifest, and previous baseline runs must not be modified, overwritten, or deleted.
3. **Enhance Discriminating Power:** The resulting 10-case benchmark must provide a dynamic range where the current baseline scores less than 100%, allowing a future agentic implementation to show a measurable delta.

## Execution Strategy

### 1. Artifact Preservation
- The original 6 cases (`data/cases/case_001` through `case_006`) are strictly frozen. No files within these directories will be altered.
- The existing manifest (`benchmark/manifest.json`), the ground truth files, and existing verification outputs from Phase 1 remain frozen.
- Previous baseline runs (e.g., `run_20260829_154058_02e9416b`) stored in `evidence/phase_2/runs/` will not be touched.

### 2. Adding New Cases
- Four new cases (`case_007` to `case_010`) will be added to `data/cases/`.
- These cases will adhere strictly to the existing schemas in `benchmark/schemas/` and the anomaly taxonomy in `benchmark/RULEBOOK.md`. No changes will be made to the schemas or the rulebook.
- The new cases will be designed to be complex enough to induce reasoning errors in a zero-shot baseline (e.g., subtle calculation errors in invoices, nuanced date discrepancies, or complex interactions between goods receipts and purchase orders).

### 3. Verification Updates
- The `scripts/validate_phase1.py` script (ground truth oracle) will be updated or run to include the new cases without altering its deterministic logic.
- A new versioned manifest (e.g., `benchmark/manifest_v3.json` or by simply re-generating the manifest to include the new hashes) will be created, ensuring the old manifest is still preserved or clearly tracked in Git history.
- The test suite (`tests/`) will be updated to expect 10 cases instead of 6. All tests must pass before the new baseline is executed.

### 4. Metrics Re-evaluation
- The primary metric remains Exact Case-Level Recommendation Accuracy.
- Once the 10 cases are established and tests pass, a new Phase 2 baseline run will be executed.
- We require the baseline to score < 100% on the expanded benchmark.

### 5. Final Re-Audit
- After generating the new baseline run and offline evaluation report, the entire pipeline (Git Bash on Windows) will be re-run in a clean clone environment.
- The remediation plan and evidence will be submitted to External ChatGPT for Phase 2 approval.

## Lock Status
Phase 3+ remains strictly **LOCKED**. No code for agentic history, failure analysis, or multi-step tool use will be written until External ChatGPT explicitly responds with `PHASE APPROVED — 100%` for this remediated Phase 2.
