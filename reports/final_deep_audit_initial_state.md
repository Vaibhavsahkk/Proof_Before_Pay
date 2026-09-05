# Final Deep Audit — Initial State (Phase 0)

**Date:** 2026-09-01 05:25 IST
**Auditor:** final deep end-to-end audit + self-remediation pass
**Purpose:** record the repository state BEFORE any remediation in this audit.

## Environment

| Item | Value |
|---|---|
| OS | Windows 10.0.26200 x64 (win32) |
| Python | 3.11.15 (venv + system) |
| Docker | 29.6.2, Compose v5.3.1 |
| Git HEAD | `9b243a82de91bbdd16beae9c53100634559a3634` (master) |
| Remote | `https://github.com/Vaibhavsahkk/Proof_Before_Pay.git` (origin/master == HEAD) |
| API keys | 5 Gemini keys in local `.env` (gitignored, verified not tracked). Free tier. One key permanently depleted (prepayment credits). |
| Provider quota state at audit start | `GenerateRequestsPerDayPerProjectPerModel-FreeTier` (20 req/day/key) exhausted on all keys from the A3 baseline runs; resets 12:30 IST 2026-09-01. A4 agent run + A5 scoring scheduled via automation `automation-a4cda0a1` at 12:38 IST. |

## Working tree (before this audit's remediation)

Modified (pre-existing, not from this audit):
- `src/agent/extraction.py` — schema-constrained extraction + deterministic normalization; predates A1, is the CURRENT agent that A4 measures (hash recorded in `evidence/phase_track_b/A4_agent_version_freeze.json`)
- `.obsidian/workspace.json` — editor state (cosmetic)
- `evidence/phase_2/scaffold_verify_powershell.txt` — CRLF-only checkout artifact (content identical to HEAD; restored during audit)

Untracked (all created by A1–A3 Track B phases + prior dev session):
- `data/track_b/evaluation/` — baseline/agent runners, prompts v1/v2 + hashes, run artifacts, evaluator
- `evidence/phase_track_b/` — A1 evidence, A2/A3 evidence, v1 defect report, A4 version freeze
- Dev-session leftovers (poisoned caches quarantined to `tmp/quarantined_dev_caches/` earlier;
  root-level dev scripts `output.json`, `test_direct.py`, `test_out*.txt`, `test_upload.py`,
  `test_output.json` quarantined during this audit Phase 0 — they were untracked, unignored
  clutter caused by a single-document dev test that also poisoned `case_101` caches)

Deleted-then-restored during earlier A-phase: `data/cache/extractions/case_001..012.json`
(were deleted by the dev session; restored via `git checkout` — working tree now matches HEAD).

## Inventory (what exists)

- **Source:** `src/agent/` (extraction, orchestrator, credentials, memory, document_adapter),
  `src/tools/` (calculator, equality, rule_evaluator), `src/utils/` (logger, human_checkpoint),
  `src/ui/` (server.py + UI assets), `src/main.py`
- **Tests:** 19 test files, 165 tests collected (0 collection errors)
- **Scripts:** validate_phase1, verify_manifest, evaluate_agent, generate_phase1/2_data,
  run_agent_phase3_5/3_7, qa_demo_environment, verify_container_security, clean-clone runners
- **Benchmark:** `benchmark/` schemas + RULEBOOK, `data/cases/public/` (12 Track A cases),
  `data/cases/ground_truth/`, `evidence/phase_1/SHA256_MANIFEST.txt`
- **Track B:** `data/track_b/` (DESIGN.md frozen, 12 frozen cases, ground truth, MANIFEST.sha256,
  verify_track_b.py, generator) + `data/track_b/evaluation/` (A2–A5 artifacts)
- **Evaluation artifacts:** baseline runs (v1 defect run + v2 runs + frozen_v2_assembly),
  agent runs (1 INVALID quota-exhaustion attempt; live A4 run pending quota reset)
- **Traces:** `traces/raw/` 611 files (gitignored), `traces/sanitized/` empty
- **Trajectories:** `trajectories/sanitized/example_trace.json` (placeholder dummy only — REAL
  trajectory package is missing; flagged for Phase 24)
- **Reports:** 60+ phase reports, HOT_TAKE, IMPROVEMENT_CHANGELOG, JUDGE_FAQ, SUBMISSION_CHECKLIST,
  video structure, reproduction designs
- **Docker:** Dockerfile (runtime/verifier targets), docker-compose.yml/.dev.yml
- **Clean clone infra:** `__clean_clone/` snapshot + `scratch/run_clean_clone.ps1` +
  `scripts/run_clean_clone_tests.ps1` (SHA-based)

## Known state at start (from the A-phase session, all documented)

- A2/A3 (Track B baseline) COMPLETE — measured baseline: 83.33% recommendation accuracy,
  75.00% findings exactness, 100% schema validity, 10.00% unsafe-PAY (1/10)
- A4/A5 pending the quota reset (scheduled automation)
- Full pytest at quota exhaustion: 147 passed / 16 failed (all 16 = live-API UI e2e tests;
  root cause: dev session had deleted Track A caches → live path → exhausted quota;
  caches since restored)

## Findings already remediated during Phase 0/1 of THIS audit

1. **Dependency declarations fixed:** `requirements.lock` was missing `pymupdf`, `pypdf`,
   `pillow` (all imported by `src/agent/document_adapter.py` and tests). Added pinned
   versions (1.28.0 / 6.14.2 / 12.3.0).
2. **CRLF checkout artifact restored:** `evidence/phase_2/scaffold_verify_powershell.txt`
   was byte-modified but content-identical (line-ending only) → `git checkout --`.
3. **Dev clutter quarantined:** root-level dev test scripts moved to
   `tmp/quarantined_dev_caches/` (untracked, out of the submission surface).
