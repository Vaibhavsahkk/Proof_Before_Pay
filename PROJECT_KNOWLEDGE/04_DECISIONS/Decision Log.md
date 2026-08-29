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
Active. Phase 1 is awaiting external review; Phase 2 is locked.

### Evidence
`PLAN.md`, `STATUS.md`, `DECISIONS.md`.
