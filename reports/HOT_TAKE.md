# HOT TAKE (DRAFT — evidence-first, no fabricated conclusions)

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Status:** DRAFT based only on observed repository evidence. All Track-B-dependent conclusions are marked **PENDING REAL MEASUREMENT**. This file must be finalized only after Phase A5 produces real numbers.

## 1. MAIN FAILURE MODE (observed, with evidence)

**Our benchmark was too easy for our own primary metric — and a fair process caught it before we could fool ourselves.**

- Observed: the fair single-pass LLM baseline (`gemini-3.6-flash`, fixed prompt, no tools, no ground-truth access) scored **100% exact recommendation accuracy** on the frozen benchmark, which mathematically caps any final-agent improvement at **0.0%** on the mandatory improvement scorecard.
- Consequence: the external gate returned exactly `PHASE FAIL` for Phase 2 (`BLOCKERS.md`, `DECISIONS.md` Decision 010, `reports/phase_2_review_packet.md`).
- The failure was a **benchmark-design failure**, not a model failure. The model did everything asked of it.
- Secondary observed failure modes (all preserved as evidence):
  - Provider model unavailability: pinned `gemini-2.5-pro` returned HTTP 404 for all cases (`DECISIONS.md` Decision 008).
  - Zero paid quota: `gemini-3.1-pro-preview` returned HTTP 429 for all cases (Decision 008).
  - Portability failure: v1 input hashes depended on Windows CRLF checkout state and broke in a fresh clone (Decision 009) — a reproducibility failure, not a scoring failure.
- **PENDING REAL MEASUREMENT:** the primary failure mode on messy real-world documents (Track-B) — the Track-B dataset, baseline score, and agent score do not exist yet (Phase A1 in progress by another agent; A2/A4/A5 not run). No claim about Track-B difficulty or improvement is made here.

## 2. WHAT WE LEARNED

1. **A "measured improvement" claim is a property of the benchmark, not the agent.** We had a working agent and still had nothing measurable to show, because the yardstick had no headroom. Designing the measurement is harder than building the system.
2. **Running the fair baseline first was the single most valuable decision.** It exposed the ceiling before any agent code existed, while fixing it was still cheap and uncontaminated by outcome-targeting.
3. **Provider failure is a first-class benchmark dimension, not an inconvenience.** Every failure mode we later hardened against (404, 429, quota exhaustion, CRLF hash drift) was actually observed in recorded evidence — which is why the failover and fail-closed behavior are justified rather than decorative.
4. **Honest ceiling reporting survives review; inflated claims would not have.** The remediation path (coverage-matrix-driven expansion from 6 to 12 cases, outcome-independent case selection, proposed secondary metrics) was approved precisely because the ceiling was reported, not hidden.
5. **Reproducibility is fragile in the small details.** A newline-normalization choice broke cross-machine evidence verification — evidence portability had to be designed (manifest v2, `utf8-text-normalized-lf`).


## 3. WHY IT MATTERS

- For judges: this project demonstrates the difference between "the agent works" and "the agent is **provably better** in a way a third party can re-measure". The 0.0% delta on the frozen benchmark is reported openly in `reports/phase_3_7_final_readiness.md` §8 rather than spun.
- For the field: agentic-system evaluations routinely saturate small synthetic benchmarks. When the baseline ties the agent, the correct response is to change the measurement under predeclared, outcome-independent rules — never to relabel structural changes as percentage wins.
- For small-business users (the target user in `docs/LOCKED_PROBLEM.md`): the value that IS already real and measured is not "better accuracy than a chat prompt" but **verifiability** — deterministic math, evidence-linked citations, fail-closed behavior, and audit traces. That value proposition stands even at equal accuracy.

## 4. WHAT WE WOULD DO DIFFERENTLY

1. **Pre-register the primary metric with a headroom analysis** before authoring a single case: estimate whether a reasonable baseline can saturate it, and require messy/unstructured inputs from day one (Track-B arrives late in our process — its results are PENDING).
2. **Treat provider failure and environment drift as benchmark requirements**, with quota-pool budgeting and newline/hash normalization specified before the first run, not after a failed clean-clone gate.
3. **Commit features before claiming freeze.** Several verified subsystems (credential failover, document adapter, UI, memory) are currently untracked in git — a submission pushed at current HEAD would omit them.
4. **Declare every dependency** (`PyMuPDF`, `Pillow`) in the lockfile the moment code imports them, so "N tests passed" is reproducible from a clean install.

## 5. WHAT THIS TEACHES ABOUT TRUSTWORTHY AGENTIC SYSTEMS

1. **Constrain what the LLM can do wrong, then prove the constraint.** The LLM only maps evidence to schemas and writes explanations; all money math is Python `Decimal` and all identity checks are exact string equality (`src/tools/`), verified per-run in trace output (`deterministic_calculation_references`).
2. **Fail closed, always.** Schema failure, extraction failure, unreadable documents, and total credential-pool exhaustion all produce `INVESTIGATE` with an explicit human next step — never a `PAY` (`src/agent/orchestrator.py`).
3. **Separate the answer key from the runtime.** Ground truth lives only in the verifier Docker target; the runtime allowlist excludes it, and a forced-failure test proves the runtime rejects an injected ground-truth mount (`verify.ps1`).
4. **Measured deltas before improvement claims.** Our current measured delta is honestly 0.0%; any nonzero claim awaits Track-B Phase A5 — **PENDING REAL MEASUREMENT**.
5. **Preserve your failures as evidence.** Invalid runs, superseded attempts, and the PHASE FAIL verdict are retained in the repository; a trustworthy system's history must be auditable, including its mistakes.

> **DO NOT FINALIZE THIS DOCUMENT UNTIL:** Track-B baseline (A2), Track-B agent (A4), and the A5 comparison have been actually measured. Replace every PENDING marker with real, cited numbers, or delete the claim.
