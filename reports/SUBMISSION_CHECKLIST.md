# Submission Checklist

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Rule:** Nothing is marked DONE without evidence. Items depending on unmeasured phases (A2/A4/A5) are explicitly PENDING and cannot be flipped to DONE by documentation work. Legend: DONE (verified today, evidence cited) / PENDING (work remains before submission) / HUMAN ACTION (cannot be automated).

## TECHNICAL

| # | Item | Status | Notes / evidence |
| --- | --- | --- | --- |
| T1 | Frozen 12-case benchmark valid | DONE | `scripts/validate_phase1.py` 12/12 oracle PASS, re-run 2026-08-31, exit 0 |
| T2 | SHA-256 manifest verified | DONE | `scripts/verify_manifest.py` PASS, re-run 2026-08-31, exit 0 |
| T3 | Committed 12-case baseline run | DONE | `evidence/phase_2/runs/run_20260830_091031_f1cc354c/` tracked in git, status VALID |
| T4 | Committed agent results + re-scoring path | DONE | `reports/phase_3_7_results.json`; `scripts/evaluate_agent_3_7.py` deterministic re-score |
| T5 | Deterministic tool core in repo | DONE | `src/tools/calculator.py`, `equality.py`, `rule_evaluator.py` (tracked) |
| T6 | Orchestrator + trace logger in repo | DONE | `src/agent/orchestrator.py`, `src/utils/logger.py` (tracked) |
| T7 | Commit untracked verified subsystems (credentials, document_adapter, memory, UI, 6 test modules) | PENDING | `git status --short` at audit time lists them untracked; freeze claims currently exceed committed state |
| T8 | Declare missing lockfile deps (`PyMuPDF`, `pypdf`, `Pillow`) | PENDING | `src/agent/document_adapter.py` imports them; full-suite collection fails locally (120 collected, 4 import errors) |
| T9 | Single reconciled full-suite pipeline pass at final SHA | PENDING | Current docs cite 46/81/110/116/132/135 inconsistently; one number must win |
| T10 | Track-B dataset + freeze (A1) | PENDING | Owned by parallel Antigravity agent; this agent must not touch `track_b/` or its scripts/tests |
| T11 | Track-B baseline run (A2) | PENDING | NOT YET MEASURED |
| T12 | Track-B agent run (A4) | PENDING | NOT YET MEASURED |
| T13 | Verification-loop feature | NOT BUILT (do not list as a capability) | If never implemented, remove all references from evidence docs |

## EVIDENCE

| # | Item | Status | Notes / evidence |
| --- | --- | --- | --- |
| E1 | Improvement changelog with real iterations only | DONE (v1) | `reports/IMPROVEMENT_CHANGELOG.md` (H1-H11 evidenced; future phases as PENDING placeholders) |
| E2 | Hot take draft | DONE (draft) | `reports/HOT_TAKE.md` — Track-B sections marked PENDING REAL MEASUREMENT |
| E3 | Evidence audit | DONE | `reports/parallel_submission_evidence_audit.md` |
| E4 | Documentation consistency audit | DONE | `reports/DOCUMENTATION_CONSISTENCY_AUDIT.md` (fixes themselves remain PENDING) |
| E5 | Rubric evidence matrix | DONE | `reports/HACKATHON_RUBRIC_EVIDENCE_MATRIX.md` |
| E6 | Judge FAQ | DONE | `reports/JUDGE_FAQ.md` (PENDING MEASUREMENT where applicable) |
| E7 | Judge reproduction design | DONE (design) | `reports/JUDGE_REPRODUCTION_DESIGN.md` — implementation/packaging not done by design |
| E8 | Apply documentation fixes (A1-A6, B1-B5, C1-C3 from consistency audit) | PENDING | Edits intentionally NOT made by this agent to avoid parallel-write conflicts |
| E9 | Representative sanitized trajectories committed | PENDING | Plan exists (`reports/REPRESENTATIVE_TRAJECTORIES_PLAN.md`); `traces/sanitized/` currently empty; only committed trace was deleted in working tree |
| E10 | Track-B measured improvement number (A5) | PENDING | NOT YET MEASURED — must replace every "PENDING A5" marker in evidence docs |
| E11 | Root `CHANGELOG.md` presence decision | PENDING | Does not exist at root; candidate content in `reports/IMPROVEMENT_CHANGELOG.md`; promotion is a human/orchestrator decision |


## VIDEO

| # | Item | Status | Notes / evidence |
| --- | --- | --- | --- |
| V1 | Evidence-first 5-minute script/structure | DONE (script) | `reports/FINAL_VIDEO_STRUCTURE.md` — hard rule: no unmeasured score claims |
| V2 | Record video at final committed HEAD | PENDING | Record only after T7-T9 complete so the demo matches the repo |
| V3 | Upload video (YouTube unlisted/Loom) | HUMAN ACTION | Needs human accounts; link goes into portal form |
| V4 | Video includes forbidden-claims review | PENDING | Verify against `reports/FINAL_VIDEO_STRUCTURE.md` checklist before upload |

## GITHUB

| # | Item | Status | Notes / evidence |
| --- | --- | --- | --- |
| G1 | Public repository URL | HUMAN ACTION | `https://github.com/Vaibhavsahkk/Proof_Before_Pay` — visibility must be set to public by the human |
| G2 | Push final state (including T7/T8 commits and reports/) | PENDING | Working tree has untracked/modified files at audit time |
| G3 | No secrets in repo | DONE (as tracked) | `.env` gitignored; trace sanitizer masks keys (`AQ.A...rXsA`); recheck after G2 before going public — HUMAN ACTION to confirm |
| G4 | README current (dead run refs, phase narrative, test counts) | PENDING | Fixes specified in `reports/DOCUMENTATION_CONSISTENCY_AUDIT.md` A1-A3 |
| G5 | REPRODUCE.md current (verify command target, clean-clone candidate) | PENDING | Fixes specified in consistency audit A1/B1 |

## PORTAL

| # | Item | Status | Notes / evidence |
| --- | --- | --- | --- |
| P1 | Repository URL entry | HUMAN ACTION | — |
| P2 | Video URL entry | HUMAN ACTION | After V3 |
| P3 | Form text (problem/solution/results) | PENDING | Draft in `reports/final_human_submission_handoff.md` §6 must be reworded per consistency audit A6 (no implied improvement claim; Track-B PENDING) before pasting |
| P4 | Submit before deadline | HUMAN ACTION | — |
| P5 | Save submission confirmation | HUMAN ACTION | Screenshot/receipt to `evidence/` |

## Item counts

- DONE: 13 (technical 6, evidence 7 — including drafts/designs whose completion is explicitly qualified)
- PENDING: 14 (including 4 that can only be closed by real measurement: T11, T12, E10, and Track-B-dependent parts of V2/V4)
- HUMAN ACTION: 7 (portal entries, video upload, repo visibility, secret recheck)

**Critical path to submission:** T7 -> T8 -> T9 -> G2/G4/G5 -> E8/E9 -> V2 -> V3/V4 -> P1-P5. In parallel (other agent): A1 -> A2 -> A4 -> A5 -> replace PENDING markers. The submission can ship honestly without Track-B numbers (all docs are written to stand on committed evidence alone), but every Track-B claim anywhere in the repo must remain PENDING until A5 produces real numbers.
