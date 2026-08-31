# IMPROVEMENT CHANGELOG

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Rule:** Every historical entry below is supported by actual repository evidence (file paths cited). Future work is a PENDING placeholder only — no future iteration is claimed to have happened. Entries must be filled ONLY after the real experiment runs and its artifacts are committed.

## Entry schema (use for every new iteration)

```
Iteration: <name / phase>
Why we changed it: <observed failure or requirement — cite evidence>
What was tested: <exact command(s)>
Expected hypothesis: <prediction written BEFORE the run>
Actual measured result: <observed numbers or NOT YET MEASURED>
Evidence: <committed file paths>
Decision: <keep / revert / iterate / stop>
What we learned: <one honest sentence>
```

## Historical iterations (all evidenced)

### Iteration H0 — Phase 1 benchmark foundation
- **Why:** the locked problem required a frozen, reproducible measurement before any model work.
- **What was tested:** schema validation, deterministic oracle, leakage checks, SHA-256 manifest, Docker runtime/verifier isolation.
- **Expected hypothesis:** a fair frozen benchmark must be valid before any baseline runs.
- **Actual measured result:** no model scores exist at this stage by design.
- **Evidence:** `reports/phase_1_review_packet.md`, `evidence/phase_1/SHA256_MANIFEST.txt`, `evidence/phase_1/final_clean_clone_execution.txt`. Re-verified offline 2026-08-31: validation and manifest PASS, 29 focused tests pass.
- **Decision:** keep; foundation approved (Decision 007).
- **Learned:** measurement design precedes system design.

### Iteration H1 — Baseline attempt: `gemini-2.5-pro`
- **Why:** a fair single-pass baseline was required (Phase 2).
- **Actual measured result:** INVALID — all six provider calls returned HTTP 404 (model unavailable to new users).
- **Evidence:** `evidence/phase_2/runs/run_20260829_151625_260ba740` (retained; see `DECISIONS.md` Decision 008).
- **Decision:** preserve as INVALID evidence; pin a concrete available model.
- **Learned:** provider availability must be probed and pinned, never assumed.

### Iteration H2 — Baseline attempt: `gemini-3.1-pro-preview`
- **Actual measured result:** INVALID — all six calls returned HTTP 429 (Pro free-tier quota zero).
- **Evidence:** `evidence/phase_2/runs/run_20260829_152146_25ba3699` (Decision 008).
- **Decision:** preserve; switch to successfully probed `gemini-3.6-flash`.
- **Learned:** quota limits are measurable benchmark constraints.

### Iteration H3 — Baseline attempt: manifest v1 hashing
- **Actual measured result:** locally VALID but superseded — clean-clone audit exposed CRLF-dependent input hashes.
- **Evidence:** `evidence/phase_2/runs/run_20260829_152514_caab4d45`, `evidence/phase_2/superseded_clean_clone_failure_c21cb36.txt` (Decision 009).
- **Decision:** supersede; canonicalize to `utf8-text-normalized-lf` (manifest v2).
- **Learned:** evidence portability across OS checkout states must be designed.

### Iteration H4 — Accepted baseline: `gemini-3.6-flash`, manifest v2
- **Actual measured result (six-case benchmark at the time):** 100% exact recommendation accuracy, 100% findings, 100% schema validity, 0/5 unsafe-PAY (`reports/phase_2_review_packet.md`).
- **Consequence:** External ChatGPT returned exactly `PHASE FAIL` — a 100% baseline leaves zero measurable primary-metric headroom for any agent.
- **Evidence:** `evidence/phase_2/runs/run_20260829_154058_02e9416b` (superseded on expansion; the run directory was later removed from git by commit `2f7602a`), `reports/phase_2_review_packet.md`, `BLOCKERS.md`, Decision 010.
- **Decision:** remediate by coverage-matrix expansion (outcome-independent), not by outcome targeting.
- **Learned:** the hardest failure to accept is a perfect score you cannot improve on.

### Iteration H5 — Benchmark expansion 6 -> 12 cases (coverage-driven)
- **Why:** taxonomy gaps in `benchmark/RULEBOOK.md` were unrepresented (Math Error, Currency Mismatch/Invalid Currency, Vendor Identity Mismatch, Missing PO Line ID, Missing Vendor Master, Verified Bank Change PAY path).
- **What was tested:** `python scripts/validate_phase1.py` (12/12 oracle PASS — re-verified 2026-08-31), `python scripts/verify_manifest.py` (PASS).
- **Evidence:** `docs/PHASE_2_COVERAGE_MATRIX.md`, `docs/PHASE_2_METRIC_AMENDMENT_PROPOSAL.md`, `reports/phase_2_1_review.md`.
- **Decision:** keep; selection rule was outcome-independent by design.
- **Learned:** expand only what the taxonomy demands.

### Iteration H6 — Accepted 12-case baseline
- **Actual measured result:** 12/12 successful; 100.0% recommendation accuracy; 100.0% findings; 100.0% schema validity; 0/10 unsafe-PAY; 121.18s total / 10.10s mean latency; 23,314 prompt + 3,095 candidate tokens; cost UNKNOWN.
- **Evidence (committed in git):** `evidence/phase_2/runs/run_20260830_091031_f1cc354c/evaluation_report.json` (status VALID), `evidence/phase_2/final_clean_clone_execution.txt`, `reports/phase_2_review_packet.md`, `STATUS.md`.
- **Decision:** accepted as the fair baseline for all agent comparisons.
- **Learned:** headroom remained at zero even after doubling coverage — the synthetic clean-JSON format favors single-pass models.


### Iteration H7 — Minimal agent (Phase 3.3) with deterministic tools
- **Why:** baseline latent risks (math fragility, attribution, fuzzy identity) justified separating LLM reasoning from exact computation (`reports/phase_3_1_baseline_failure_analysis.md`).
- **What was tested:** unit/integration tests for orchestrator and tools.
- **Evidence:** `src/agent/orchestrator.py`, `src/tools/*`, `tests/test_phase3_3_orchestrator.py`, `tests/test_phase3_3_tools.py`, `reports/phase_3_3_implementation.md`.
- **Decision:** keep; one agent + deterministic tools (Decision 004).
- **Learned:** the LLM earns its place only where semantics are genuinely required (extraction, explanation).

### Iteration H8 — First agent evaluation (Phase 3.4)
- **Actual measured result:** 12/12 exact recommendation and findings correctness; unsafe-PAY 0/10 (see `reports/phase_3_4_valid_evaluation.md`, `reports/phase_3_4_metric_and_evaluator_audit.md`).
- **Structural flaws found and documented:** static (false) evidence citations; static tool references; over-inclusive missing-evidence mapping (`reports/phase_3_5_final_metric_integrity_review.md` §2).
- **Decision:** iterate on attribution, not on accuracy (accuracy already at ceiling).
- **Learned:** the evaluator must measure what the agent can actually get wrong.

### Iteration H9 — Agent optimization (Phase 3.5): dynamic attribution
- **Why:** Phase 3.4 emitted hardcoded citations for documents not present in a case (false citations), e.g. `prior_payment_history` cited when null.
- **What was changed:** `evidence_references` built dynamically from the extracted bundle; `deterministic_calculation_references` recorded from real tool-call hooks; `missing_evidence` mapped from a strict root-document set (fixing `case_010` misclassification).
- **Actual measured result:** recommendation accuracy/findings/unsafe-PAY unchanged (100% / 100% / 0.0%); structural false citations eliminated (classified as a structural improvement, NOT a percentage gain — `reports/phase_3_5_final_metric_integrity_review.md`).
- **Evidence:** `reports/phase_3_5_agent_optimization.md`, `reports/phase_3_5_evaluation_report.json`, `reports/phase_3_5_final_metric_integrity_review.md`.
- **Decision:** keep.
- **Learned:** report structural improvements as structural — never convert them into invented percentages.

### Iteration H10 — Robustness/safety hardening (Phase 3.6-3.7)
- **What was tested:** adversarial tests (prompt-injection resistance, container isolation, fail-closed defaults); 110 tests passing at SHA `6183e4f9` (per `reports/phase_3_7_final_readiness.md`).
- **Actual measured result:** final metrics 100.0% / 100.0% / 0.0% unsafe-PAY on 12 cases; **measured baseline-vs-agent delta: 0.0% on all shared metrics** (documented honestly in `reports/phase_3_7_final_readiness.md` §8).
- **Evidence:** `reports/phase_3_6_robustness_and_safety.md`, `reports/phase_3_7_results.json`, `reports/phase_3_7_final_readiness.md`.
- **Decision:** keep; freeze; pursue messy-real-world inputs (Track-B) to create real headroom.
- **Learned:** safety and traceability are improvements that the primary metric cannot see — which is exactly why secondary metrics were proposed.

### Iteration H11 — Runtime dependency fix (Phase 4.8 remediation, DEF-01)
- **Why:** `python-dotenv` was missing from `requirements.lock`, breaking the runtime container; clean-clone (V-14) and live-run (V-15) were unverified.
- **Actual measured result:** fix committed (`c1bc2b8`); clean-clone run reproduced 113 passed / 2 environment-only failures; live run under real 429 quota exhaustion failed closed to `INVESTIGATE` with zero unsafe PAYs.
- **Evidence:** `reports/phase_4_8_runtime_and_reproducibility_remediation.md`.
- **Decision:** keep.
- **Learned:** a single undeclared dependency invalidates every "it works on my machine" claim.

## PENDING entries (DO NOT fill until the real experiment is run and evidenced)

### PENDING — Track-B dataset creation (Phase A1)
- **Status:** PENDING — in progress by the Antigravity agent in parallel; NOT touched by this agent. `track_b/`, `scripts/generate_track_b.py`, `scripts/verify_track_b_manifest.py`, `tests/test_track_b_freeze.py` are reserved for that agent's exclusive use.
- **Actual measured result:** NOT YET MEASURED.

### PENDING — Track-B baseline run (Phase A2)
- **Expected hypothesis (pre-registered now, before any run):** a single-pass LLM baseline on messy real-world documents (noise, omissions, unstructured text) is expected to score BELOW 100% on exact recommendation accuracy, creating measurable headroom for the agent. **This is a hypothesis only — not a result.**
- **Actual measured result:** NOT YET MEASURED. **Evidence:** none yet.

### PENDING — Track-B agent run (Phase A4)
- **Actual measured result:** NOT YET MEASURED. **Evidence:** none yet.

### PENDING — Headline improvement comparison (Phase A5)
- **Planned comparison:** Track-B baseline metrics vs Track-B agent metrics on identical frozen inputs; primary metric exact case-level recommendation accuracy; safety guardrail unsafe-PAY rate; plus structural metrics (attribution, tool traceability, completeness) where applicable.
- **Actual measured result:** NOT YET MEASURED. Any percentage claimed before this runs is fabrication.

### PENDING — Verification-loop experiments
- **Status:** a verification/self-correction loop is NOT IMPLEMENTED. If it is never implemented, this entry must be deleted, not filled. **Actual measured result:** NOT YET MEASURED.

> **Integrity rule:** if an experiment listed as PENDING is never run, delete its entry before submission rather than leaving an implied result. An empty honest changelog beats a fabricated one.
