# Judge Reproduction Design

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Status:** DESIGN ONLY — nothing implemented, no scripts written, no commands from this design executed beyond the read-only verification already documented in `reports/parallel_submission_evidence_audit.md`. No cached or fake results created. Phases A2-A5 NOT executed.

## 1. Design goal

A single documented workflow that lets a hackathon judge, from a clean clone and WITHOUT any API key, in under 15 minutes: (1) validate the frozen benchmark, (2) validate the Track-B freeze, (3) re-score the committed frozen outputs, (4) reproduce the headline comparison, (5) inspect representative trajectories, and (6) run the relevant offline tests. Live-API reproduction is a clearly separated, optional path.

## 2. Existing machinery this design reuses (all verified present in the repository today)

| Existing capability | Artifact | Verified status (2026-08-31) |
| --- | --- | --- |
| Frozen benchmark validation + deterministic oracle (12 cases) | `scripts/validate_phase1.py` | PASS, exit 0, 12/12 |
| SHA-256 manifest verification | `scripts/verify_manifest.py` | PASS, exit 0 |
| Focused Phase 1 test suite | `tests/test_phase1_validation.py`, `tests/test_manifest.py` | 29 passed |
| Phase 2 baseline test suite | `tests/test_phase2_baseline.py` | 35 tests collectable |
| Offline committed-baseline report verification | `python -m eval.evaluate_baseline <run_dir> --verify-existing` | Documented in `REPRODUCE.md`; deterministic, no API |
| Agent results re-scoring against ground truth | `scripts/evaluate_agent.py` (Phase 3.5 results), `scripts/evaluate_agent_3_7.py` (Phase 3.7 results) | Read committed JSON, score against `data/cases/ground_truth/`; no API |
| Docker pipelines (runtime/verifier separation, forced ground-truth-injection rejection) | `verify.ps1`, `verify.sh` | Documented; Docker required |
| Trace/trajectory policy guard | `verify.ps1`/`verify.sh` tracked-traces check | Enforces sanitized-only trace commits |
| Clean-clone harness | `scripts/run_clean_clone_tests.ps1` | Exists; recorded candidates predate the 12-case run (see audit §2.5) |
| **Track-B freeze validation** | `scripts/verify_track_b_manifest.py`, `tests/test_track_b_freeze.py` (RESERVED for the A1 agent — not yet present) | **PENDING PHASE A1 — DO NOT create, run, or modify these** |

## 3. Proposed judge workflow (to be packaged later; design only)

### STEP 0 — Clean clone
```powershell
git clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git judge_check
cd judge_check
git log --oneline -3   # confirm submitted HEAD
```
**OFFLINE REPRODUCIBLE** (network needed only for the clone itself).

### STEP 1 — Validate frozen benchmark [OFFLINE REPRODUCIBLE]
```powershell
python scripts/validate_phase1.py
python scripts/verify_manifest.py
```
Expected (re-observed 2026-08-31): `ALL PHASE 1 VALIDATIONS PASSED` (12/12 oracle) and `Manifest verification passed.`, both exit 0.

### STEP 2 — Validate Track-B freeze [OFFLINE REPRODUCIBLE — PENDING PHASE A1]
```powershell
python scripts/verify_track_b_manifest.py
python -m pytest tests/test_track_b_freeze.py -q
```
**STATUS: PENDING.** Track-B artifacts do not exist yet; A1 is owned by the parallel Antigravity agent. This step is included in the design so the final reproduction guide can be complete, but it must NOT be authored, executed, or verified by this agent. Expected outputs must be filled by the A1/A5 owners with real observed text only.

### STEP 3 — Re-score frozen outputs [OFFLINE REPRODUCIBLE]
```powershell
# 3a. Verify the committed 12-case baseline run (no API call):
python -m eval.evaluate_baseline evidence/phase_2/runs/run_20260830_091031_f1cc354c --verify-existing

# 3b. Re-score the committed agent results against hidden ground truth:
python scripts/evaluate_agent_3_7.py     # scores reports/phase_3_7_results.json
```
Expected: baseline report evaluation status VALID (100% / 100% / 100% / 0/10 unsafe); agent re-score 100.0% / 100.0% / 0.0%. **These expectations come from committed artifacts and were re-runnable offline today; the actual judge run must print its own fresh output.**

### STEP 4 — Reproduce the headline comparison [OFFLINE REPRODUCIBLE for frozen results; LIVE for new runs]
- **Frozen comparison (offline):** the committed `evaluation_report.json` vs `scripts/evaluate_agent_3_7.py` output yields the honest headline: baseline 100% vs agent 100% on the frozen 12-case benchmark, **measured delta 0.0%**, plus structural improvements (dynamic evidence attribution, real tool traceability, correct missing-evidence mapping) per `reports/phase_3_5_final_metric_integrity_review.md`.
- **Track-B headline comparison:** **PENDING PHASE A5 — NOT YET MEASURED.** When A5 exists, this step becomes "run the Track-B evaluator on frozen Track-B outputs (offline)". Until then, no Track-B number may appear anywhere in the reproduction story.
- **Fresh live runs (optional, LIVE API DEPENDENT):** requires `GEMINI_API_KEY` in the local process env only; `python -m baseline.run_baseline` then `python -m eval.evaluate_baseline <new_run_id>`; agent: `python -m src.main --run-all`. Quota limits apply; the 5-key pool with failover exists for this path.

### STEP 5 — Inspect representative trajectories [OFFLINE REPRODUCIBLE]
```powershell
# curated, sanitized trajectories (see reports/REPRESENTATIVE_TRAJECTORIES_PLAN.md):
Get-Content trajectories/sanitized/<T1..T6>.json
Get-Content traces/sanitized/<sanitized-trace>.jsonl
```
**STATUS: PENDING — the curated set is not yet committed (see audit §3.3).** This design step becomes executable only after the authorized packaging step described in the trajectories plan. Judges can meanwhile view a live trace in the UI's Audit tab when running the server locally.

### STEP 6 — Run relevant offline tests [OFFLINE REPRODUCIBLE; Docker needed for full pipelines]
```powershell
python -m pytest tests/test_phase1_validation.py tests/test_manifest.py tests/test_phase2_baseline.py -q
.\verify.ps1      # full Docker pipeline (Windows) — also proves runtime/verifier isolation
& 'C:\Program Files\Git\bin\bash.exe' ./verify.sh   # POSIX pipeline via Git Bash
```
**Known pre-fix requirement:** `PyMuPDF` (fitz), `Pillow`, and (in some local venvs) `python-dotenv` must be installed/declared for the full local suite; the local audit environment collected 120 tests with 4 module import errors due to missing `fitz`/`dotenv`. The Docker pipelines install from `requirements.lock` and must be the authoritative test path — which makes declaring `PyMuPDF`/`Pillow` in the lockfile a REQUIRED FIX before judge reproduction of the full suite (documented in `reports/DOCUMENTATION_CONSISTENCY_AUDIT.md`).

## 4. Classification summary

| Workflow step | Classification | API key needed | Current state |
| --- | --- | --- | --- |
| Clean clone + HEAD check | Offline (clone needs network) | No | Ready |
| Validate frozen benchmark (12 cases + manifest) | OFFLINE REPRODUCIBLE | No | Verified today, exit 0 |
| Validate Track-B freeze | OFFLINE REPRODUCIBLE | No | PENDING PHASE A1 (reserved for other agent) |
| Verify committed baseline report | OFFLINE REPRODUCIBLE | No | Command documented; deterministic |
| Re-score committed agent outputs | OFFLINE REPRODUCIBLE | No | Command documented; deterministic |
| Headline comparison (frozen benchmark) | OFFLINE REPRODUCIBLE | No | Committed; honest 0.0% delta |
| Headline comparison (Track-B) | OFFLINE (frozen outputs) once A5 exists | No | PENDING PHASE A5 |
| New baseline/agent runs | LIVE API DEPENDENT | Yes (`GEMINI_API_KEY`, local env only) | Optional; quota-limited |
| Trajectory inspection | OFFLINE REPRODUCIBLE | No | PENDING curated sanitized set |
| Focused offline tests | OFFLINE REPRODUCIBLE | No | 29 passed today |
| Full Docker pipelines | OFFLINE REPRODUCIBLE (local Docker) | No | Documented; needs lockfile fix for UI/adapter modules |

## 5. Non-negotiable integrity rules for whoever implements this design

1. Never commit generated "judge output" files as if they were results; the judge's own console output is the evidence.
2. Never present a live-API run as offline-reproducible, or vice versa.
3. Never fill STEP 2 or the Track-B comparison with expected numbers before A1/A5 artifacts exist.
4. Any change to `requirements.lock` needed for the full suite must be a small, single-purpose, separately verified commit — not mixed with this design's documentation.
5. This design document itself adds no code and no cached results; it stays a design.

