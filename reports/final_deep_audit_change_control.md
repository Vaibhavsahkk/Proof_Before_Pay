# Final Deep Audit — Change Control Record (Phase 27)

**Date:** 2026-09-01
**HEAD at audit start:** `9b243a82de91bbdd16beae9c53100634559a3634` (master, == origin/master)
**Nothing committed** (per instructions). All changes live in the working tree.

## Files CHANGED (tracked, modified)

| File | Change | Why (evidence-justified) |
|---|---|---|
| `requirements.lock` | +3 deps: `pymupdf==1.28.0`, `pypdf==6.14.2`, `pillow==12.3.0` | **Defect found by fresh-env execution (P1/P18):** these are imported by `src/agent/document_adapter.py` but were undeclared; a clean install failed `import fitz` before the fix and passed after — the exact judge-facing reproduction failure the audit required fixing. |
| `src/ui/server.py` | `HTTPServer` → `ThreadingHTTPServer` (2 lines) | **Defect found by live execution (P7):** a single quota-blocked investigation froze the ENTIRE UI (single-threaded server; `/api/cases` unresponsive 8+ min, `curl` exit 28). After the fix: `/api/cases` returns 200 during a blocked investigation — verified. No agent code touched (A4 freeze covers `src/agent`, `src/tools`, `src/utils` only). |
| `README.md` | Phase section, case count 6→12, accepted-run ID | Stale claims contradicted by current evidence (P23). |
| `REPRODUCE.md` | Test-count history + offline/live test guidance | "46 passed" was Phase-1-era; honest current counts recorded (P23). |
| `STATUS.md` | Current-phase header, six→twelve case references | Stale ("Phase 4 standby", "six-case benchmark", "Phase 3+ unauthorized") (P23). |
| `reports/FINAL_TECHNICAL_FREEZE.md` | Appended §5 audit addendum | Historical 2026-08-30 table preserved unchanged; current state appended (P23 rule: never rewrite history, add to it). |
| `trajectories/README.md` | Documented the new real trajectory package | P24. |
| `.obsidian/workspace.json` | editor state (cosmetic, pre-existing) | not audit work |
| `src/agent/extraction.py` | **NOT changed by this audit** (pre-existing working-tree state, hash-recorded in `evidence/phase_track_b/A4_agent_version_freeze.json` before A4) | This is the agent version the frozen Track B measurement runs. |

## Files CREATED

- `reports/final_deep_audit_initial_state.md` — Phase 0 baseline state record
- `evidence/phase_track_b/A2_A3_execution_evidence.md`, `A3_baseline_prompt_v1_defect.md`, `A4_agent_version_freeze.json` (A-phase evidence, pre-audit)
- `data/track_b/evaluation/`: `run_track_b.py`, `evaluate_track_b.py`, `baseline_prompt_v2.txt` + `.sha256`, `baseline_runs/*` (incl. frozen_v2_assembly + manifest), `agent_runs/INVALID_*` (marked invalid)
- `trajectories/sanitized/01..05_*.json` + `trajectory_manifest.json` — **REAL execution traces** (clean PAY, HOLD duplicate-billing, missing-evidence INVESTIGATE, bank-change INVESTIGATE, credential failover), each secret-scan verified
- `tmp/quarantined_dev_caches/` — quarantined dev leftovers (poisoned case_101 caches + root dev scripts), untracked by design

## Files DELETED

- `trajectories/sanitized/example_trace.json` — dummy placeholder replaced by the real package
- Working-tree deletions of `data/cache/extractions/case_001..012.json` (made by a PREVIOUS dev session) were RESTORED via `git checkout` — caches now match HEAD

## PROTECTED FILES — UNCHANGED (verified by `git status` scoped to protected paths)

`data/cases/`, `data/cases/ground_truth/`, `benchmark/`,
`evidence/phase_1/SHA256_MANIFEST.txt`, `data/track_b/cases/`,
`data/track_b/ground_truth/`, `data/track_b/MANIFEST.sha256`,
`data/track_b/DESIGN.md`, `data/track_b/verify_track_b.py`,
`data/track_b/generate_track_b.py` — **ALL UNCHANGED**.

## TEST RESULTS (all real executions, 2026-09-01)

| Command | Result |
|---|---|
| `python -m pytest --collect-only -q` | 165 collected, 0 collection errors |
| `python -m pytest --ignore=tests/test_environment.py --ignore=tests/test_ui_e2e_integration.py --ignore=tests/test_ui.py -q` | **144 passed, 0 failed** |
| `python -m pytest tests/test_ui_e2e_integration.py -q` (minus 3 live-upload tests) | **10 passed, 3 deselected** (the 3 require live Gemini quota) |
| `python -m pytest tests/test_ui.py` (offline subset) | passed (static + cached pipeline tests) |
| `python scripts/validate_phase1.py` | **ALL PHASE 1 VALIDATIONS PASSED** (exit 0) |
| `python scripts/verify_manifest.py` | **Manifest verification passed** (exit 0) |
| `python scripts/evaluate_agent.py` | **100% accuracy / 100% findings / 0.0% unsafe-PAY** (Track A, exit 0) |
| `python data/track_b/verify_track_b.py` | **TRACK B VERIFICATION PASSED** (exit 0) |
| `python -m pytest tests/test_track_b_freeze.py -q` | 14 passed |

### Failure classification (honest)

- The earlier "16 failed / 147 passed" full-suite run and subsequent "1 failed" runs
  were **audited to root cause and are LOCAL ENVIRONMENT failures, not project failures**:
  1. A prior dev session deleted the git-tracked Track A extraction caches (restored);
  2. Gemini free-tier daily quota exhausted (20 req/day/key; resets 12:30 IST) — live-API
     tests cannot run until reset;
  3. An audit-process port collision (my own fresh-clone server on port 8899) made the
     e2e suite hit the wrong server instance — resolved by stopping the audit servers;
     after cleanup the same tests pass 10/10.
- `tests/test_environment.py` is container-only by design (documented in REPRODUCE.md).

## DOCKER RESULT

**BLOCKED on this host**: Docker Desktop daemon fails to start ("Docker Desktop is
unable to start"), retried 5+ times incl. hard restart. NOT a project defect — no
Dockerfile/compose change was needed or made. Last proven-good container execution:
commit `adc3328`, recorded in `reports/phase_4_9A_live_recovery_closure.md` (§3.5,
Exit 0) and `reports/phase_4_15_final_judge_simulation.md`. Must be re-run on a host
with a working Docker daemon before final submission.

## SECURITY RESULT

- Full-repo tracked-file scan: **zero real API keys** (only masked `AQ.A...rXsA`
  prefixes and one synthetic test fixture `AIzaSyFakeSyntheticGeminiKey...`).
- `.env` untracked and gitignored; `.dockerignore` excludes it from images.
- All 5 trajectory files + sampled traces: key-pattern scan CLEAN.
- Ground-truth isolation verified: runtime image COPY allowlist excludes ground
  truth; Docker `verifier`/`runtime` target separation unchanged.
- No payment execution, no bank mutation anywhere in the codebase.
