# APPROVED DECISIONS

## Decision 001 — Locked problem
Chosen project: **Evidence-Driven Pre-Payment Exception Investigator for Small Businesses**.

Scope:
- investigate suspicious supplier invoices
- reconcile invoice, PO, GRN, vendor record, prior history, and payment-change evidence
- verify financial calculations with deterministic code
- produce evidence-linked findings
- output PAY / HOLD / INVESTIGATE as a recommendation for human review

Not in scope:
- automatic payment execution
- declaring a supplier fraudulent
- replacing banks, ERP systems, or enterprise AP platforms
- production financial integration before the core benchmark is proven

## Decision 002 — Phase gating
No phase transition without:
Antigravity acceptance → Local ChatGPT READY → External ChatGPT `PHASE APPROVED — 100%`.

## Decision 003 — Evidence policy
Observed execution beats narrative claims. Any result without command/output/artifact evidence is `UNVERIFIED`.

## Decision 004 — Architecture policy
Start with one primary agent plus deterministic tools. Add extra agents only when an observed failure requires them.

## Decision 005 — Conditional model provider
If a model API becomes necessary in a later approved phase, the Gemini API will be used.

- No model API is required or authorized during Phase 0.
- No Gemini API call must be made during Phase 0.
- GEMINI_API_KEY must only be supplied through a local environment variable or approved secret store.
- A real GEMINI_API_KEY must never enter Git, logs, traces, evidence files, or chat.
- OpenAI and Anthropic APIs are not selected for this project.

## Decision 006 — Phase 0 Approval
External ChatGPT returned the exact verdict `PHASE APPROVED — 100%`. Tested Phase 0 candidate: 49358817c8481ca0bf3eaa6b5b1d2ddaa015cf96. Phase 1 authorized.

## Decision 007 — Phase 1 Approval
External ChatGPT returned exactly `PHASE APPROVED — 100%` for Phase 1. Tested Phase 1 candidate: 43ba9356aaa110113e81a446cb701bee40f0fc39. Evidence snapshot: adf9a1c1032df5679717acf8691691decc638f49. Phase 2 Fair Baseline is authorized. Phase 3+ remains locked.
