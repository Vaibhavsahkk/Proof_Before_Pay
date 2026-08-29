# Decision Log

## Runtime and Verifier Images Are Separate

### Date
2026-08-29

### Decision
The Dockerfile uses a `runtime` target for future baseline/agent execution and a `verifier` target for tests, evaluator code, and hidden ground truth.

### Reason
The runtime must not receive the answer key. An explicit runtime COPY allowlist is easier to audit than copying the whole repository.

### Current Status
Active and verified.

### Evidence
`Dockerfile`, `docker-compose.yml`, `tests/test_phase1_validation.py`, commit `b9cf9da107c4839c7a8481788c2a0356dab53b83`.

---

## Ground Truth Validation Remains Strict

### Date
2026-08-29

### Decision
Ground-truth schema, count, and oracle checks run in the verifier target. They are not bypassed when the verifier executes.

### Reason
The verifier intentionally contains the hidden answer key; only the runtime excludes it. This preserves strict benchmark validation without leaking labels to the future baseline or agent.

### Current Status
Active and verified.

### Evidence
`scripts/validate_phase1.py`, `tests/test_phase1_validation.py`, `Dockerfile`, and both verification pipelines.

---

## Exact USD Currency Scope

### Date
2026-08-29

### Decision
Phase 1 cases require invoice and PO currency to be exactly `USD`. Any other currency is an `Invalid Currency` HOLD finding.

### Reason
The current benchmark needs one unambiguous currency scope before baseline evaluation.

### Current Status
Active and verified.

### Evidence
`benchmark/RULEBOOK.md`, schemas, oracle, and currency tests.

---

## Strict Phase-Gated Progression

### Date
Verified from `PLAN.md`.

### Decision
No work may proceed to a subsequent phase until External ChatGPT returns the exact string `PHASE APPROVED — 100%`.

### Reason
Preserve scope, evidence quality, and auditability.

### Current Status
Active. Phase 1 is externally approved, Phase 2 Fair Baseline is active, and Phase 3+ is locked.

### Evidence
`PLAN.md`, `STATUS.md`, `DECISIONS.md`.

---

## Phase 2 Baseline Model Availability

### Date
2026-08-29

### Decision
Pin the valid baseline retry to `gemini-3.6-flash` rather than a mutable `latest` alias.

### Reason
The first real attempt observed provider HTTP 404 for all six 2.5 Pro calls. The next 3.1 Pro attempt observed HTTP 429 because this account's Pro free-tier quota is zero. A minimal non-benchmark health probe to provider-recommended `gemini-3.6-flash` returned exit 0 and the exact expected model identifier.

### Current Status
Active. The failed attempt is retained as INVALID operational evidence and is not a performance result.

### Evidence
`DECISIONS.md` and the two INVALID run directories under `evidence/phase_2/runs/`.

---

## Canonical Phase 2 Input Hashing

### Date
2026-08-29

### Decision
Use manifest `phase2-baseline-run-v2` and hash UTF-8 public-case text after universal newline normalization.

### Reason
A real clean-clone check proved that raw-byte hashes from a Windows CRLF checkout were not portable to an LF checkout. Canonical hashing binds semantic input content without hiding byte-level output tampering.

### Current Status
Active and verified by the accepted v2 run and exact remote clean-clone gate.

### Evidence
`DECISIONS.md`, `evidence/phase_2/superseded_clean_clone_failure_c21cb36.txt`, and `evidence/phase_2/final_clean_clone_execution.txt`.
