# Documentation Consistency Audit

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Scope inspected:** `README.md`, `STATUS.md`, `PLAN.md`, `REPRODUCE.md`, root `CHANGELOG.md` (does not exist), `docs/`, `reports/`, plus ground-truth verified facts from live offline commands (see `reports/parallel_submission_evidence_audit.md` §1).
**Rule:** REPORT ONLY. No file was rewritten by this audit. Each finding gives FILE / PROBLEM / CURRENT CLAIM / ACTUAL EVIDENCE / RECOMMENDED UPDATE.

## Priority 1 — contradictions that would mislead a judge

### A1
- **FILE:** `README.md` (lines 92, 98), `REPRODUCE.md` (line 111)
- **PROBLEM:** References an evidence run directory that no longer exists in the repository.
- **CURRENT CLAIM:** "The accepted Phase 2 run is `evidence/phase_2/runs/run_20260829_154058_02e9416b`" and the offline verify command targets it.
- **ACTUAL EVIDENCE:** `git ls-files evidence/phase_2` shows only `run_20260830_091031_f1cc354c` is tracked; commit `2f7602a Remove old baseline runs` removed `run_20260829_154058_02e9416b`. The directory does not exist on disk; the documented verify command would fail.
- **RECOMMENDED UPDATE:** Point to `evidence/phase_2/runs/run_20260830_091031_f1cc354c` (12 cases, VALID) in both files and update the six-case metrics text (0/5 unsafe) to the 12-case metrics (0/10 unsafe).

### A2
- **FILE:** `README.md` (lines 21-23) vs `STATUS.md` (lines 3-7)
- **PROBLEM:** Contradictory current-phase claims between the two most authoritative status files.
- **CURRENT CLAIM:** README says "Phase 2 ... is the only active phase. Phase 3+ remains locked"; STATUS.md says "Current phase: Phase 4 — Minimal Agent V1 ... Standby for Phase 5 instructions".
- **ACTUAL EVIDENCE:** Phase 3 and 4 work is done and evidenced (dozens of Phase 3/4 reports; agent implemented; 100% 12-case evaluation); Phase 5 is locked.
- **RECOMMENDED UPDATE:** Pick ONE authoritative phase narrative (recommend: "Phase 4 complete and frozen; Phase 5+ locked; parallel Track-B/A-phases in preparation") and mirror it in both files.

### A3
- **FILE:** `README.md` (line 83) vs `STATUS.md` (line 34) vs `REPRODUCE.md` (line 75)
- **PROBLEM:** Three different "expected" test counts for pipelines; no count matches a single current reconciled suite.
- **CURRENT CLAIM:** README: "Expected focused result: 29 tests pass"; REPRODUCE Phase 1 section: "46 passed" for full pipelines; STATUS: "81 tests" for both Docker pipelines.
- **ACTUAL EVIDENCE:** Today: 29 focused Phase 1 tests PASS (verified); `tests/test_phase2_baseline.py` collects 35; full local collection = 120 tests + 4 import errors (missing `fitz`/`dotenv` in local venv); documented historical full-suite counts range 110 / 113 / 116 / 132 / 135 across phase reports.
- **RECOMMENDED UPDATE:** After committing the untracked test modules and declaring `PyMuPDF`/`Pillow` in `requirements.lock`, re-run the full pipeline once and update ALL files to that single number with its date and SHA.

### A4
- **FILE:** `reports/FINAL_TECHNICAL_FREEZE.md`
- **PROBLEM:** "100% SUBMISSION READY" freeze claims contradict actual git state.
- **CURRENT CLAIM:** "Clean working tree" (Git Provenance row), failover/UI/adapter subsystems "frozen", "135 passed".
- **ACTUAL EVIDENCE:** `git status --short` at audit time shows modified `src/agent/extraction.py`, `src/agent/orchestrator.py`, `evidence/phase_1/final_clean_clone_execution.txt`, `reports/phase_3_3_results.json`; deleted `traces/sanitized/trace_20260828_131408_7428b4c6.jsonl`; and UNTRACKED `src/agent/credentials.py`, `src/agent/document_adapter.py`, `src/agent/memory.py`, `src/ui/`, six test modules, and several reports.
- **RECOMMENDED UPDATE:** Either commit the pending work and re-run verification to re-earn the freeze claim, or retitle the document as a point-in-time snapshot (with its SHA) that predates these changes.

### A5
- **FILE:** `reports/final_human_submission_handoff.md` (§1) vs `reports/HUMAN_SUBMISSION_CHECKLIST.md` (intro)
- **PROBLEM:** Two different "frozen/approved HEAD" SHAs in the two submission documents.
- **CURRENT CLAIM:** Handoff: "Approved HEAD: `39dbee561632ba8ac5b0bf91999326a0b938c5da`"; Checklist: "frozen and audited ... HEAD: `6861c0714f1435ceaa9252951dd11e57c00ff985`".
- **ACTUAL EVIDENCE:** Current HEAD is `adc33289e6272496d769fc8b26fb43e34b529a1e`; neither cited SHA equals HEAD or each other.
- **RECOMMENDED UPDATE:** Update both to the final submitted HEAD at submission time, in one consistent edit.

### A6
- **FILE:** `reports/final_human_submission_handoff.md` (§6 "Measured Results", §9)
- **PROBLEM:** Form text implies agent-vs-baseline improvement that was not measured.
- **CURRENT CLAIM:** "achieving 100% recommendation accuracy (0% Unsafe-PAY rate) compared to a frozen baseline" — reads as a comparison claim.
- **ACTUAL EVIDENCE:** Baseline ALSO measured 100% (`evidence/phase_2/runs/run_20260830_091031_f1cc354c/evaluation_report.json`); the measured delta is 0.0% (`reports/phase_3_7_final_readiness.md` §8).
- **RECOMMENDED UPDATE:** Reword to "matching the fair baseline at 100% with structural improvements in evidence attribution and tool traceability; measured improvement on Track-B: PENDING".


## Priority 2 — stale details

### B1
- **FILE:** `REPRODUCE.md` ("Phase 2 verification" section)
- **PROBLEM:** Clean-clone candidate predates the accepted 12-case run.
- **CURRENT CLAIM:** "The current accepted candidate is verified with: run_clean_clone_tests.ps1 -CandidateSha `1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c` -Phase phase_2".
- **ACTUAL EVIDENCE:** Commit graph: `1ffb2281` (record portable Gemini baseline) precedes `fab26ac` (Add new 12-case baseline run). The clean-clone gate therefore could not have covered the currently accepted run directory.
- **RECOMMENDED UPDATE:** After final commit, re-run the clean-clone gate against the final SHA and update the recorded candidate + normalized log SHA-256.

### B2
- **FILE:** `reports/phase_2_review_packet.md`
- **PROBLEM:** Describes a superseded six-case run as the accepted run (packets are historical, but this file is linked from README as current decision evidence).
- **CURRENT CLAIM:** Run `run_20260829_154058_02e9416b`, 6/6 cases, SDK `google-genai==2.19.0`, "6/6 SUCCESS".
- **ACTUAL EVIDENCE:** That run directory was removed from git (commit `2f7602a`); the accepted committed run is `run_20260830_091031_f1cc354c` with 12/12, SDK `2.20.0` (per its `run_manifest.json`).
- **RECOMMENDED UPDATE:** Either mark the packet explicitly as superseded-by-remediation historical evidence, or add a header pointing to the 12-case successor packet.

### B3
- **FILE:** `benchmark/README.md` ("Synthetic Data Guarantee")
- **PROBLEM:** Stale case count.
- **CURRENT CLAIM:** "There are 6 cases provided in `data/cases/public/`".
- **ACTUAL EVIDENCE:** 12 public cases and 12 ground-truth cases exist and pass the oracle (`scripts/validate_phase1.py`, 12/12, re-verified 2026-08-31).
- **RECOMMENDED UPDATE:** Change to 12 cases (and mention the 6->12 coverage-matrix expansion).

### B4
- **FILE:** `PROJECT_KNOWLEDGE/09_PROGRESS/Improvement Changelog.md`
- **PROBLEM:** Stale "Agent iterations | NOT RUN - later phases locked" row contradicts completed Phases 3-4.
- **ACTUAL EVIDENCE:** Phase 3.4/3.5/3.7 agent evaluations exist with committed results (`reports/phase_3_7_results.json` etc.).
- **RECOMMENDED UPDATE:** Supersede this note with the new root-level `reports/IMPROVEMENT_CHANGELOG.md` (created by this agent) or update the vault note to point at it.

### B5
- **FILE:** `README.md` ("Current Evidence" list)
- **PROBLEM:** Missing entries for current evidence.
- **CURRENT CLAIM:** Evidence list cites phase_1/phase_2 items and `reports/phase_2_review_packet.md` only.
- **ACTUAL EVIDENCE:** Current decision evidence also includes `reports/phase_3_7_results.json`, `reports/phase_4_evaluation_report.json`, and (once committed) the Phase 4.x reports.
- **RECOMMENDED UPDATE:** Extend the evidence list; remove the dead run reference (A1).

## Priority 3 — real reproducibility defects (not just prose)

### C1
- **FILE:** `requirements.lock`
- **PROBLEM:** Undeclared runtime imports.
- **CURRENT CLAIM:** The lockfile fully defines runtime dependencies (`google-genai`, `jsonschema`, `python-dotenv`).
- **ACTUAL EVIDENCE:** `src/agent/document_adapter.py` imports `fitz` (PyMuPDF), `pypdf`, and `PIL` (Pillow); several test modules import them too. They are absent from `requirements.lock`. Today's local collection: 120 tests collected, 4 module import errors (`ModuleNotFoundError: fitz`, `dotenv`).
- **RECOMMENDED UPDATE:** Add pinned `PyMuPDF`, `pypdf` (if used), and `Pillow` to `requirements.lock` in a single-purpose commit; re-run full pipeline. (This agent did NOT modify the lockfile.)

### C2
- **FILE:** `data/cases/ground_truth;C/` (directory on disk)
- **PROBLEM:** A stray second ground-truth directory with a `;C` suffix exists on disk (12 case files) alongside the real `data/cases/ground_truth/`.
- **ACTUAL EVIDENCE:** `Get-ChildItem data/cases` shows both directories; `git ls-files data/cases` tracks ONLY `data/cases/ground_truth/...`; `git status` does not list the stray directory.
- **RECOMMENDED UPDATE:** Investigate and delete the stray directory (likely a shell-quoting accident during a past operation). Do NOT commit it. This agent did not touch it.

### C3
- **FILE:** Root-level `CHANGELOG.md`
- **PROBLEM:** Expected by the submission brief; does not exist at repo root.
- **ACTUAL EVIDENCE:** No root `CHANGELOG.md`; the only changelog is the stale vault note (B4).
- **RECOMMENDED UPDATE:** Promote `reports/IMPROVEMENT_CHANGELOG.md` (created by this agent) — either copy to root `CHANGELOG.md` at submission time or reference it from README. Decision belongs to the human/orchestrating agent.

## Priority 4 — stale labels seen in reports (lower stakes; historical snapshots)

- `reports/phase_4_9_live_failover_verification.md` §16: "116 passed" — a point-in-time count; fine if dated/SHA-stamped, misleading if read as current.
- `reports/phase_4_13_small_business_usability_audit.md` §5: "132/132" — same caveat (and this file is currently UNTRACKED).
- `reports/phase_4_15_final_judge_simulation.md` §2: "135 passed in 15.56s" — same caveat.
- `reports/phase_4_8_complete_system_audit.md`: "110 items" reference superseded by later suite growth.
- **RECOMMENDED UPDATE:** Do not edit history reports; instead ensure README/STATUS carry the single current number (A3) and that each historical report keeps its SHA+date header so counts are unambiguous snapshots.

## Note on files NOT audited for staleness

`docs/PHASE_2_*`, `reports/phase_*` packets, and `PROJECT_KNOWLEDGE/` are phase-historical records; their internal claims were spot-checked only where README/STATUS treat them as current evidence (A1, B1, B2). `PLAN.md` is a governance plan, not a status claim, and was checked for consistency with the phase narrative (it is fine as a plan).
