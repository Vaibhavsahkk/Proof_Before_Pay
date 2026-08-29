# Phase 2 Remediation Plan

## Context
During the external review of Phase 2 (Fair Baseline), the benchmark received a `PHASE FAIL` verdict because the baseline agent achieved exactly 100% Exact Case-Level Recommendation Accuracy on the existing 6-case frozen benchmark. 

The external reviewer ruled this a benchmark-design blocker: 100% baseline accuracy leaves zero measurable headroom for demonstrating agentic improvement (which is the primary metric and a mandatory scorecard item for the hackathon).

## Objectives
1. **Expand the Benchmark via Coverage Matrix:** Evaluate expanding the benchmark to a target of 10 or more cases by developing a coverage matrix. The expansion must be justified independently by the matrix over already-approved evidence types, anomaly taxonomy (`benchmark/RULEBOOK.md`), precedence, safety boundary, and realistic workflow gaps.
2. **Preserve Immutability:** Existing artifacts must remain exactly as they are. The existing six public cases (`data/cases/public/case_001.json` through `case_006.json`), the six ground-truth files (`data/cases/ground_truth/case_001.json` through `case_006.json`), the Phase 1 manifest (`evidence/phase_1/SHA256_MANIFEST.txt`), and all prior runs and metrics must be preserved exactly.
3. **Avoid Outcome Targeting:** Cases must never be selected, removed, or revised based on baseline success/failure. We will not force or require the baseline to score below 100%. The amended benchmark and metric will be frozen first, then the baseline will be run once. Whatever result occurs will be preserved and reported. If it remains a ceiling, we will preserve it and revisit evaluation design transparently.

## Execution Strategy

### 1. Predeclared Coverage Matrix (Next Authorized Action)
- The next authorized action is the design and local review of a coverage matrix and metric amendment proposal ONLY. 
- No new cases, code, test expectation changes, manifest regeneration, or Gemini calls are authorized yet.

### 2. Adding New Cases
- Any new cases will adhere strictly to the existing schemas in `benchmark/schemas/` and the approved anomaly taxonomy in `benchmark/RULEBOOK.md`. No unapproved anomalies (e.g., date discrepancies) will be invented or introduced.
- There will be an explicit independent case-authoring and ground-truth review separation before the baseline is granted access, as far as practicable given the already-known ceiling result.

### 3. Verification Updates
- The `scripts/validate_phase1.py` script (ground truth oracle) will be updated or run to include the new cases without altering its deterministic logic.
- A new versioned manifest will be created, ensuring the old manifest is still preserved or clearly tracked in Git history.
- The test suite (`tests/`) will be updated to reflect the expanded case count. All tests must pass before the new baseline is executed.

### 4. Metrics Re-evaluation
- The primary metric remains Exact Case-Level Recommendation Accuracy unless formally amended.
- Once the expanded cases are established and tests pass, a new Phase 2 baseline run will be executed.
- The result of the baseline run will be recorded objectively without targeting a specific outcome.

### 5. Final Re-Audit
- After generating the new baseline run and offline evaluation report, the entire pipeline (Git Bash on Windows) will be re-run in a clean clone environment.
- The remediation plan and evidence will be submitted to External ChatGPT for Phase 2 approval.

## Lock Status
Phase 3+ remains strictly **LOCKED**. No code for agentic history, failure analysis, or multi-step tool use will be written until External ChatGPT explicitly responds with `PHASE APPROVED — 100%` for this remediated Phase 2.
