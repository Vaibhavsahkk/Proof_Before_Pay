# Phase A2 + A3 Execution Evidence — Track B Baseline

**Date:** 2026-08-31 / 2026-09-01
**Executor:** hackathon evaluation agent (urgent execution mode, Phase A Track B)
**Repo:** `D:\Proof Before Pay\MICRO.1` (git HEAD `9b243a82de91bbdd16beae9c53100634559a3634`, branch master)

---

## A2 — Fair Baseline: STOP CHECK (PASSED)

| Check | Evidence |
|---|---|
| Baseline implemented | `data/track_b/evaluation/run_track_b.py` (`--mode baseline`): one direct multimodal Gemini call per case — every `bundle.json` document attached in native format (PDF/PNG as multimodal parts, JSON as text). No tools, no orchestration, no rulebook, no second pass. |
| Prompt frozen + hash-pinned | v1: SHA-256 `3CA82D5AD74C1608DBA8663B34873BC8029C0F42191F37C2BFE22A4397B7EA36`; v2: SHA-256 `4E1E2853E9E5A0B3C2C62487938D72C6E84278D57855D4025ED27451878E3E16`. Runner refuses to execute if the prompt file does not match its recorded hash (verified live at every run start). |
| Model/settings per A1 §7 | `gemini-3.6-flash`, temperature 0.0, `response_mime_type=application/json`, max_output_tokens 4096 — identical envelope for every case. Recorded in every run manifest and every case record. |
| Input isolation | Runner reads ONLY `data/track_b/cases/<case>/bundle.json` + the documents it lists. Static audit: zero code-level references to `ground_truth`, evaluator files, agent traces, agent outputs, Track A answer files. Leakage rules of the frozen dataset verified by `verify_track_b.py`. |
| Cache isolation | `check_cache_isolation()` asserts no Track A extraction cache entry can collide with `case_101..112` and the ID spaces are disjoint. This check caught a real integrity problem (see "Integrity events" below). |
| Baseline smoke test | `run_20260831_212134_2e04c889` (v1 prompt) and `run_20260831_213825_800742a8` (v2 prompt): case_101 → SUCCESS, recommendation PAY, findings [], schema valid, all 4 documents attached, returned model `gemini-3.6-flash`. |
| No Track A modification | `scripts/validate_phase1.py` → ALL PHASE 1 VALIDATIONS PASSED; `scripts/verify_manifest.py` → Manifest verification passed (run 2026-08-31 ~21:00 UTC and after). |
| No Track B modification | `data/track_b/verify_track_b.py` → TRACK B VERIFICATION PASSED (manifest, oracle re-derivation, generator determinism) — run before and after every sub-phase. `tests/test_track_b_freeze.py` → 14 passed. |

## Integrity events found and handled (honest record)

1. **Poisoned dev cache (pre-existing, NOT frozen data).** `data/cache/extractions/case_101.json` +
   `data/cache/explanations/case_101.json` (+ `case_998/999/TEST-01` explanation entries) were
   untracked leftovers from single-document dev testing (`test_direct.py` fed only `invoice.pdf`,
   so the cached extraction has PO/GRN/vendor_master = null while the frozen case has 4 documents).
   The runner's own collision check refused to start, proving the guard works. The poisoned files
   were **quarantined** (not deleted) to `tmp/quarantined_dev_caches/`. The root `output.json` dev
   artifact shows a wrong case_101 result caused by this cache — it is a dev artifact, not an
   evaluation artifact, and is excluded from A4/A5.
2. **Baseline prompt v1 defect (found by A3 run 1, BEFORE any scoring).** v1 paraphrased the output
   contract without including the schema/enum, so every findings case produced free-text findings
   and failed schema validation (8/12 SCHEMA_INVALID in run `run_20260831_212344_ef2cfd1a`).
   Documented in `evidence/phase_track_b/A3_baseline_prompt_v1_defect.md`. v1 file + hash remain
   frozen as evidence. v2 = v1 + official output contract inline (rulebook still excluded per
   A1 §7). v2 was created and hash-frozen BEFORE the first scored run.
3. **API unavailability.** Transient 503 "high demand" and per-key 429s occurred throughout
   (recorded verbatim per A3.3; no outputs substituted). Final per-key diagnosis:
   `GenerateRequestsPerDayPerProjectPerModel-FreeTier` (20 requests/day/key on
   `gemini-3.6-flash`); one key permanently depleted (prepayment credits). The daily budget
   was consumed by: v1 full run (36 attempts) + v2 runs (35 attempts) + retry probes.
   A4 agent execution was consequently **rescheduled to the quota reset** (2026-09-01 12:38 IST)
   via automation `automation-a4cda0a1`; an earlier agent smoke attempt that hit total quota
   exhaustion produced only the documented fail-closed fallback and was marked INVALID
   (`data/track_b/evaluation/agent_runs/INVALID_run_20260831_221016_46be0f5a/INVALID_MARKER.json`)
   — it is excluded from evaluation.

## A3 — Baseline Execution: STOP CHECK (PASSED with documented assembly)

**Policy (A3.3):** transient-only retry, max 3 attempts/case, key rotation + 60s cooldown on 429,
exponential backoff on 5xx — applied identically to every case. Failures recorded verbatim.

**v2 runs executed (all 12 frozen cases each):**
- `run_20260831_213900_9339c075` — 9/12 SUCCESS (101, 105, 106 transient API errors)
- `run_20260831_215742_40aab84f` — 10/12 SUCCESS (101, 102 transient API errors)
- `run_20260831_220754_384c5cf0` — case_101 retry attempt (API error)
- `run_20260831_220935_4b39378e` — case_101 retry attempt (SUCCESS)

**Frozen baseline set:** `data/track_b/evaluation/baseline_runs/frozen_v2_assembly/`
(complete-coverage assembly; every record copied verbatim from its own run with
`source_run_id` recorded; `assembly_manifest.json` holds per-case provenance + SHA-256;
no output edited). Assembly rule documented in the manifest itself. **All 12 cases SUCCESS.**

| Check | Result |
|---|---|
| Every frozen case has a baseline result | 12/12 SUCCESS records (from v2 runs) |
| No case manually edited | Assembly copies are byte-identical to their source records (hashes in manifest) |
| No case silently omitted | All 12 present; assembly manifest lists each with source run |
| Prompt hash recorded | v2 `4E1E2853E9E5A0B3C2C62487938D72C6E84278D57855D4025ED27451878E3E16` in every record |
| Run manifests recorded | Every individual run dir has its own `run_manifest.json` + the assembly manifest |
| Input hashes match frozen dataset | Every case record has `input_hash` over bundle+document SHA-256s; frozen dataset integrity re-verified after runs |
| Official benchmark still passes | validate_phase1 + verify_manifest re-run after A3: PASS |

## Baseline results (offline dry-run against frozen ground truth — pre-A5 diagnostic)

| Metric | Value |
|---|---|
| Recommendation accuracy | 10/12 = **83.33%** |
| Findings exactness | 9/12 = **75.00%** |
| Schema validity | 12/12 = **100.00%** |
| Unsafe-PAY | 1/10 = **10.00%** (case_103, duplicate billing missed) |

Per-case misses: `case_103` (HOLD→PAY, duplicate billing not detected from remittance PDF),
`case_111` (HOLD→INVESTIGATE, duplicate billing missed, bank-change found),
`case_110` (findings incomplete: found Currency Mismatch, missed Invalid Currency —
recommendation still correct).

These are the real measured baseline numbers pending A5 official scoring; the A5 evaluator
(`data/track_b/evaluation/evaluate_track_b.py`) recomputes them deterministically from the
frozen artifacts (OFFLINE RE-SCORING — no live provider calls).

## Full pytest suite status (2026-09-01, quota-exhausted state)

`python -m pytest --ignore=tests/test_environment.py -q` → **16 failed, 147 passed (772.54s)**.

Classification (per the phase instructions, LOCAL ENVIRONMENT FAILURE vs PROJECT FAILURE):

- **147 passed** — the complete offline suite: Track B freeze tests (14), manifest, phase-1
  validation, phase-2 baseline contract, phase-3 tools/orchestrator/adversarial,
  credential failover, document adapter, human checkpoint, logger, UI unit tests.
- **16 failed** — all in `tests/test_ui_e2e_integration.py` (UI end-to-end flows through
  `/api/investigate`). Root cause chain (local environment):
  1. A prior dev session deleted the git-tracked Track A extraction caches
     (`data/cache/extractions/case_001..012.json` showed as `D` in `git status`),
     forcing the UI e2e tests onto the live Gemini path;
  2. the Gemini free-tier daily quota was exhausted (see Integrity event 3 above),
     so live calls failed / hung in retry loops.
- Remediation already applied: `git checkout -- data/cache/extractions/` restored all 12
  committed caches (working tree again matches HEAD for `data/cache/`).
  `data/cache/explanations/case_001.json` + `case_012.json` were never committed — they
  self-populate on the first successful live run (expected after the quota reset).
- `tests/test_environment.py` is excluded by design (requires the Linux Docker container).

The full-suite re-run after the quota reset (scheduled with A4) is expected to restore the
previously-recorded 163-passed state; if any failure remains at that point it must be
re-classified as a project failure and reported.
