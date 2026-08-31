# JUDGE FAQ

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Rule:** Every answer below cites only evidence that exists in the repository today. Where the evidence does not exist yet, the answer says **PENDING MEASUREMENT** — we do not guess.

### 1. Why is this agentic?
The `AgentOrchestrator` (`src/agent/orchestrator.py`) runs a perception-decision loop over an evidence bundle: it observes what documents actually exist, extracts them, then dynamically decides WHICH deterministic checks are runnable (vendor identity only if vendor master present; duplicate billing only if history exists), records performed vs skipped checks, applies precedence rules, routes failures (429 -> credential rotation -> same-stage resume), and fails closed to INVESTIGATE when it cannot complete. Behavior depends on the state of the evidence, not a fixed path — that's the agentic property, and every step is in the JSONL trace.

### 2. Why not just use ChatGPT?
A single-pass prompt cannot prove where its answers came from. Our own baseline (same model, fixed prompt, no tools) hit 100% accuracy on the frozen benchmark — yet Phase 3.4/3.5 audits found it cannot evidence-attribute, and the single-pass design has documented latent risks: hallucinated arithmetic on strict `0.01`-tolerance decimal checks, unprovable citations, and fuzzy-identity guessing (`reports/phase_3_1_baseline_failure_analysis.md` §6, `reports/phase_3_5_final_metric_integrity_review.md` §2). The architecture exists to make those failure modes structurally impossible, not to out-score a chat prompt on 12 easy cases.

### 3. Why deterministic tools?
Because money math and identity checks must be exactly right. `DecimalCalculator` (Python `Decimal`, `ROUND_HALF_UP`), `EqualityChecker` (exact string equality), and `RuleEvaluator` (precedence HOLD > INVESTIGATE > PAY) are in `src/tools/`. The trace records every call under `deterministic_calculation_references`, so a reviewer can verify that no number was produced by the LLM.

### 4. What does the LLM actually do?
Exactly two things: (1) `extract` — map messy/unstructured evidence (JSON or PDF/image text via `DocumentAdapter`) into the strict extraction schema; (2) `explain` — produce the plain-English `uncertainty` and `required_human_next_step` fields. It never computes totals, never decides PAY/HOLD/INVESTIGATE, and never sees ground truth.

### 5. What happens when evidence is missing?
Fail-safe, explicitly. If a document is absent, the dependent check is recorded as SKIPPED (not guessed), and a root-document gap becomes a finding: e.g. `case_011` (no vendor master) yields `Missing Vendor Master` -> `INVESTIGATE` with a `required_human_next_step`. The strict root-document set means line-item anomalies like `Missing PO Line ID` (case_010) do NOT falsely populate `missing_evidence` (fixed in Phase 3.5; see `reports/phase_3_5_final_metric_integrity_review.md` §2.3).

### 6. What happens during API failure?
Four-layer observed behavior: (a) transient errors -> SDK retry policy; (b) `429 RESOURCE_EXHAUSTED` -> the credential slot moves to COOLDOWN/EXHAUSTED, `RetrySignal` is raised, the pool rotates to the next key, and the SAME case resumes at the SAME stage with state preserved (`src/agent/credentials.py`, `reports/phase_4_9A_live_recovery_closure.md` — real 429s, real rotation, same-point resume); (c) all keys exhausted -> fail-closed `INVESTIGATE` with finding "All credentials exhausted" (`src/agent/orchestrator.py`); (d) any other exception -> fail-closed `INVESTIGATE` "Extraction or System Failure" — observed live under real quota exhaustion (`reports/phase_4_8_runtime_and_reproducibility_remediation.md` V-15). No failure path can emit PAY.


### 7. Why can't the system execute payment?
By locked design, not just configuration: `docs/LOCKED_PROBLEM.md` forbids payment execution, bank-detail changes, fraud labeling, and external payment instructions; there is no payment API, no bank integration, and no mutating endpoint anywhere in the codebase. The output is an advisory contract; every recommendation routes to a human (`src/utils/human_checkpoint.py`).

### 8. What makes Smart Review different from Guided Cases?
Guided Cases are the 12 frozen public benchmark cases (`data/cases/public/`) with hidden ground truth — fixed inputs, exact scoring. Smart Review is the same pipeline applied to a NEW document the user uploads (PDF/PNG/JPG/JSON via `DocumentAdapter`), with NO anomaly pre-selected: the agent must discover which checks apply from the evidence alone (see `verify_smart_review_gatekeeper.py` checks 1-4 and `reports/smart_review_auto_detection_audit.md`). In short: Guided = regression-tested benchmark path; Smart = zero-hint generalization path.

### 9. How do you prevent hallucinated math?
Structurally: the LLM's extraction output is numbers-as-strings; every arithmetic operation (`multiply`, `sum_values`, `calculate_tax`, `check_equality`) is executed by `DecimalCalculator` with strict scale-2 `ROUND_HALF_UP` semantics. The output contract records which tools ran. If extraction fails or returns garbage, the run fails closed. On the frozen benchmark this is also why the agent's `case_007` (Math Error) detection is tool-verified rather than model-mental-arithmetic.

### 10. How is benchmark integrity protected?
Five mechanisms, all verifiable: (1) SHA-256 manifest (`evidence/phase_1/SHA256_MANIFEST.txt`) checked by `scripts/verify_manifest.py` — passed today; (2) deterministic oracle re-derives ground truth (`scripts/validate_phase1.py`, 12/12 PASS today); (3) Docker build separation — the runtime image's allowlist physically excludes `data/cases/ground_truth/`, tests, evaluator, and evidence; (4) `verify.ps1`/`verify.sh` prove the runtime REJECTS an injected ground-truth mount (forced-failure scanner exit 1); (5) the evaluator computes metrics only in the verifier image against hidden ground truth. Superseded runs are retained, never edited.

### 11. How is the baseline defined?
A fair single-pass baseline: same provider, pinned concrete model `gemini-3.6-flash`, fixed prompt (`baseline/prompt_v1.txt`), no tools, no agent loop, no ground-truth access, temperature 0.0, JSON response mode; manifest v2 with `utf8-text-normalized-lf` hashing; committed raw responses + evaluation report at `evidence/phase_2/runs/run_20260830_091031_f1cc354c/` (status VALID). Two 404/429 failed provider attempts and a CRLF-hash-superseded run are preserved as history, excluded from metrics.

### 12. How will improvement be measured?
Primary metric: exact case-level recommendation accuracy on frozen cases; safety guardrail: unsafe-PAY rate; secondary metrics (proposed in `docs/PHASE_2_METRIC_AMENDMENT_PROPOSAL.md`, used in audits): evidence-attribution correctness, finding completeness, deterministic-calculation correctness, calibrated escalation. On the current frozen 12-case benchmark the MEASURED delta is 0.0% (baseline and agent both 100%). The real improvement measurement is on Track-B (messy real-world documents): **PENDING MEASUREMENT** — Track-B baseline (A2), agent (A4), and comparison (A5) have not been run; no number will be claimed before they exist.


### 13. What was the biggest failure?
The Phase 2 gate failure: the fair baseline achieved 100% on the six-case benchmark, leaving zero measurable headroom on the mandatory improvement metric — an external `PHASE FAIL` verdict we keep in the repo (`BLOCKERS.md`, `DECISIONS.md` Decision 010). It was a benchmark-design failure, caught by process, fixed by taxonomy-driven expansion (6 -> 12 cases) and now Track-B — not by softening the metric. Secondary failures preserved as evidence: 404 model unavailability, 429 quota exhaustion, CRLF-dependent hash drift (Decision 008/009).

### 14. What was removed or rejected during development?
Governed rejections (with reasons): automatic payment execution and bank mutation (locked boundary); OpenAI/Anthropic providers (Decision 005); mutable model alias `gemini-pro-latest` in favor of a pinned ID (Decision 008); outcome-targeted benchmark cases (remediation plan forbids selecting cases by expected baseline failure); v1 raw-byte input hashing (replaced by normalized text hashing, Decision 009); Phase 3.4's static evidence citations and static tool references (replaced by dynamic verification in 3.5); `Missing PO Line ID` misclassification as missing evidence (strict root-document set). Additional "do not build" list: multi-agent swarms, chatbot interface, vector DB/RAG, decorative UI animation, duplicate business logic (see `reports/DO_NOT_BUILD.md`).

### 15. Why should a small business trust the result?
Because trust here is structural, not statistical: every recommendation is evidence-linked to the specific documents that were present; every number is deterministic and re-checkable in the trace; missing evidence is reported as missing, never guessed; the system cannot move money or change bank details; and it fails closed to "human review required" on any failure. The 12-case results are synthetic-benchmark results — we do not claim production performance, and the honest 0.0% delta is reported rather than inflated. A judge or user can re-verify all frozen results offline without an API key (see `reports/JUDGE_REPRODUCTION_DESIGN.md`).
