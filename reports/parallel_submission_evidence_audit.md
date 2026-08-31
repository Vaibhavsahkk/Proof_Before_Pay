# Parallel Submission Evidence Audit

**Prepared by:** Parallel Evidence / Submission Preparation Agent (read-only role)
**Date:** 2026-08-31
**Repository HEAD at audit time:** `adc33289e6272496d769fc8b26fb43e34b529a1e`
**Scope:** Audit of EXISTING submission evidence only. No implementation, benchmark, Track-B, `src/`, `tests/`, or `evidence/` files were modified. Phases A2-A5 were NOT executed. No API was called. Nothing was scored.

## 1. Method and commands actually executed during this audit

All commands below are offline, read-only, and were executed on 2026-08-31 to confirm which evidence claims still hold:

| Command | Observed result |
| --- | --- |
| `python scripts/validate_phase1.py` | `ALL PHASE 1 VALIDATIONS PASSED`, exit 0, 12/12 oracle match |
| `python scripts/verify_manifest.py` | `Manifest verification passed.`, exit 0 |
| `python -m pytest tests/test_phase1_validation.py tests/test_manifest.py -q` | `29 passed`, exit 0 |
| `python -m pytest tests/test_phase2_baseline.py --collect-only -q` | `35 tests collected` |
| `python -m pytest --collect-only -q` (full suite, local venv) | `120 tests collected, 4 errors` (`ModuleNotFoundError: fitz`, `dotenv` in 4 local test modules) |
| `git status --short` | Modified: `src/agent/extraction.py`, `src/agent/orchestrator.py`, `evidence/phase_1/final_clean_clone_execution.txt`, `reports/phase_3_3_results.json`; Deleted: `traces/sanitized/trace_20260828_131408_7428b4c6.jsonl`; many untracked files (see §3) |

Any value that has not been measured is marked **NOT YET MEASURED** or **PENDING PHASE A5**.

## 2. Evidence inventory by rubric dimension

### 2.1 Problem & User Value — status: EXISTS (PARTIAL strength)
- `docs/LOCKED_PROBLEM.md` — locked problem, target user (small-business AP staff/owners), hard safety boundaries.
- `benchmark/RULEBOOK.md` — anomaly taxonomy and recommendation precedence (HOLD > INVESTIGATE > PAY).
- `reports/phase_4_13_small_business_usability_audit.md` (UNTRACKED in git) — personas ("Ramesh", "Sarah"), 9-point task verification, plain-language matrix, WCAG claims.
- `PLAN.md` — phase-gated plan linking problem to evidence requirements.
- **Missing:** any external/user validation; all data is synthetic; no production-applicability evidence.


### 2.2 Agent Solution & Engineering — status: EXISTS, with a critical commit-state gap
- `src/agent/orchestrator.py` (tracked, modified in working tree) — 7-stage pipeline (EXTRACT -> VERIFY -> APPLY RULES -> EXPLAIN -> VALIDATE -> ESCALATE) inside a state-preserving `RetrySignal` recovery loop; fail-closed `INVESTIGATE` on pool exhaustion and on system failure.
- `src/tools/` (tracked) — `DecimalCalculator`, `EqualityChecker`, `RuleEvaluator` (deterministic core).
- `src/utils/logger.py` (tracked) — `TraceLogger` with recursive sanitization, secret-pattern redaction, masked credentials.
- `src/agent/credentials.py`, `src/agent/document_adapter.py`, `src/agent/memory.py`, `src/ui/` — multi-key failover, PDF/image/JSON intake, memory, reviewer UI: **all UNTRACKED in git at audit time**. The failover/UI/adapter features exist on disk but are NOT in committed history; a judge cloning current HEAD would not receive them.
- `tests/` — 17 test files on disk (10 tracked modules + 6 untracked modules + README). Local full-suite collection currently fails on 4 modules due to undeclared/local-missing dependencies (`PyMuPDF`, `python-dotenv`).
- **Missing:** committed state of the Phase 4 features; a full-suite pass at a single reconciled SHA re-verified end-to-end.

### 2.3 End-to-End Quality — status: EXISTS (committed), re-run NOT performed in this audit
- Accepted 12-case baseline run COMMITTED in git: `evidence/phase_2/runs/run_20260830_091031_f1cc354c/` with `evaluation_report.json` (`evaluation_status: VALID`; 100% recommendation accuracy, 100% findings, 100% schema validity, 0/10 unsafe-PAY; latency 121.18s total / 10.10s mean; 23,314 prompt / 3,095 candidate tokens; cost UNKNOWN).
- Agent results COMMITTED: `reports/phase_3_7_results.json` (12 case outputs with evidence references, deterministic calculation references, missing evidence, human next steps) and `reports/phase_4_evaluation_report.json` (same metrics, 12/12).
- `reports/phase_3_7_final_readiness.md` — case-by-case manual validation of all 12 outputs.
- Focused offline tests re-verified TODAY: 29 Phase 1 tests pass; manifest passes; 12-case oracle passes.
- **Missing:** a fresh live agent run re-verified at current HEAD (API-dependent; not performed); Track-B (messy real-world document) quality — NOT YET MEASURED.


### 2.4 Measured Improvement — status: EXISTS but currently measures ZERO delta (honest)
- Measured, committed fact: baseline 100.0% vs agent 100.0% exact recommendation accuracy on the frozen 12-case benchmark — **measured delta 0.0%** (`reports/phase_3_7_final_readiness.md` §8 records this explicitly).
- Measured structural (non-percentage) improvements, documented in `reports/phase_3_5_final_metric_integrity_review.md`: evidence attribution changed from a static hardcoded list to dynamic verification (eliminating false citations to absent documents); deterministic tool references changed from static strings to runtime-verified hooks; missing-evidence mapping fixed so `case_010` no longer reports a false missing document.
- **Missing (all marked NOT YET MEASURED):** Track-B baseline score (A2), Track-B agent score (A4), Track-B improvement delta (A5), any verification-loop result (feature NOT IMPLEMENTED), cost comparison (cost UNKNOWN).

### 2.5 Reproducibility — status: EXISTS, with stale references and a dependency gap
- Exists: `REPRODUCE.md`, `verify.ps1` / `verify.sh` Docker pipelines, `scripts/run_clean_clone_tests.ps1` harness, SHA-256 manifest (verified today), Dockerfile runtime/verifier separation with allowlists, offline baseline re-verification mode (`--verify-existing`).
- Gaps found today:
  - `README.md` and `REPRODUCE.md` still cite removed run `run_20260829_154058_02e9416b` (deleted from git by commit `2f7602a Remove old baseline runs`).
  - `REPRODUCE.md` Phase 1 section still says "46 passed" for full pipelines; `STATUS.md` says 81 tests. No single current number exists.
  - The recorded clean-clone candidate `1ffb2281...` predates the commit that added the accepted 12-case run (`fab26ac Add new 12-case baseline run`), so the recorded clean-clone PASS cannot have covered the currently accepted run directory.
  - `PyMuPDF` (fitz) and `Pillow` are imported by `src/agent/document_adapter.py` and four test modules but are NOT declared in `requirements.lock`; the local `.venv` is additionally missing the declared `python-dotenv`. A fresh install from `requirements.lock` currently cannot run the full suite.
  - Native macOS/Linux execution remains unverified (documented honestly).

### 2.6 Hot Take / Insights — status: EXISTS (benchmarked honesty), Track-B insight PENDING
- Fully documented governance event: Phase 2 external `PHASE FAIL` because the fair baseline hit the 100% ceiling, leaving zero measurable primary-metric headroom (`BLOCKERS.md`, `DECISIONS.md` Decision 010, `docs/PHASE_2_REMEDIATION_PLAN.md`, `reports/phase_2_review_packet.md`).
- Documented provider-failure story: `gemini-2.5-pro` HTTP 404, `gemini-3.1-pro-preview` HTTP 429, both preserved as INVALID evidence (`DECISIONS.md` Decision 008); CRLF-dependent v1 hashing superseded (Decision 009).
- Latent-fragility analysis of the single-pass baseline: `reports/phase_3_1_baseline_failure_analysis.md` §6 (math fragility, cross-document context risk, fuzzy-identity risk).
- **Missing:** the Track-B failure-mode insight — **PENDING REAL MEASUREMENT** (Track-B dataset and scores do not exist yet; A1 in progress by another agent, not touched).


## 3. Cross-cutting evidence risks (observed via `git status --short`)

1. **Untracked feature code:** `src/agent/credentials.py`, `src/agent/document_adapter.py`, `src/agent/memory.py`, `src/ui/`, `tests/test_credential_failover.py`, `tests/test_document_adapter.py`, `tests/test_phase5_memory.py`, `tests/test_ui*.py`, and multiple Phase 4 reports are untracked. Claims in `reports/FINAL_TECHNICAL_FREEZE.md` (failover, UI, "clean working tree") are not reflected in committed git state.
2. **Modified after freeze claims:** `evidence/phase_1/final_clean_clone_execution.txt` and `reports/phase_3_3_results.json` are modified in the working tree.
3. **Trajectory deliverable gap:** the only real trace ever committed (`traces/sanitized/trace_20260828_131408_7428b4c6.jsonl`) is deleted in the working tree; `trajectories/sanitized/example_trace.json` is a dummy placeholder. `traces/raw/` is gitignored by policy. **No real trajectory is currently committed.**
4. **No root `CHANGELOG.md` exists** (Part 8 of the submission brief expects one). The nearest changelog is `PROJECT_KNOWLEDGE/09_PROGRESS/Improvement Changelog.md`, which is stale ("Agent iterations | NOT RUN").

## 4. What this audit did NOT do

- Did NOT run or score anything (no A2-A5, no baseline/agent scoring, no API calls).
- Did NOT modify Track-B (does not exist in the repository yet), `data/cases/`, `benchmark/`, `evidence/`, `src/`, `tests/`, or any existing file.
- Did NOT verify live behavior; only offline, committed, and on-disk artifacts were inspected.

## 5. Bottom line

Strong, committed evidence exists for problem definition, deterministic engineering, a fair 12-case benchmark, and end-to-end agent correctness on the frozen benchmark — plus an unusually honest record of a zero-delta primary metric and structural-only improvements. The largest evidence gaps are: (1) uncommitted Phase 4 features, (2) no real committed trajectory, (3) no measurable improvement delta, and (4) stale/contradictory documentation. Items (1), (2), and (4) are actionable before submission; item (3) awaits Phase A5 measurement and must not be fabricated.
