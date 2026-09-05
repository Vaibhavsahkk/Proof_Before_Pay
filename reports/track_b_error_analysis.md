# Track B Error Analysis (A5) — classified from real run records

All classifications below are derived from the frozen run artifacts
(`data/track_b/evaluation/{baseline_runs/frozen_v2_assembly, agent_runs/frozen_v1_assembly}`)
and the frozen ground truth. No error is forced into a category the evidence
does not support.

## Summary

| System | Recommendation errors | Findings-exactness errors | Unsafe-PAY |
|---|---|---|---|
| Baseline (v2) | 2 (case_103, case_111) | 3 (+case_110) | 1 (case_103) |
| Agent | 3 (case_102, case_109, case_112) | 5 (+case_108, case_110) | 0 |

## Agent errors — one root cause dominates

**Class: extraction error → false positive (fail-closed direction).**

Pattern (identical in case_102, case_109, case_112): the extracted invoice
items contain `item_id` and `line_total` but NOT `quantity`/`unit_price`.
The deterministic check `qty × price == line_total` then throws
`CalculatorError` (missing operands) → "Math Error" → HOLD. Evidence:

- case_102 extracted items: `[{"item_id": "PAPER-A4", "line_total": "500.00"},
  {"item_id": "PEN-BL", "line_total": "50.00"}]` — ground truth: 40 × 12.50
  and 20 × 2.50 (arithmetic is perfectly consistent; the values simply never
  reached the calculator).
- case_109: `[{"item_id": "GASKET-9", "line_total": "600.00"}]` — GT: 8 × 75.00.
- case_112: `[{"item_id": "HVAC-SVC", "line_total": "450.00"}]` — GT: 2 × 225.00.

Sub-classification per case:
- case_102 (GT: PAY, clean): **false positive**, pure extraction error.
- case_109 (GT: INVESTIGATE, Vendor Identity Mismatch): the agent's identity
  finding was REAL and correct, but the false Math Error raised the severity
  to HOLD. Error class: extraction error compounding a correct finding —
  severity error caused by extraction, not reasoning.
- case_112 (GT: INVESTIGATE, Missing GRN + Missing Vendor Master): both
  findings real and correct; false Math Error again escalated to HOLD.

Findings-only errors (recommendation still correct):
- case_110 (GT: Currency Mismatch + Invalid Currency): agent found both
  correct findings PLUS a false Math Error (same extraction pattern in one
  item).
- case_108 (GT: Missing PO): agent added "Missing PO Line ID" — an artifact
  of the same rule path (PO absent ⇒ per-line PO ids unverifiable); the
  recommendation remained INVESTIGATE, correct.

**Direction of failure matters:** every agent error escalates toward HOLD
(over-cautious). None produced an unsafe PAY. In payment-review terms the
agent's failure mode is "ask a human unnecessarily," not "approve a bad
payment."

## Baseline errors — reconciliation misses

- case_103 (GT: HOLD, Duplicate Billing): **cross-document reconciliation
  failure**. The duplicate evidence was a prior identical invoice embedded in
  the remittance-advice PDF; the one-prompt model recommended PAY. This is
  the single **unsafe-PAY** of the evaluation (paid a non-payable case).
- case_111 (GT: HOLD, Duplicate Billing + Unverified Bank Change):
  **missing-evidence handling / severity error** — found the bank change
  (INVESTIGATE) but missed the embedded duplicate billing entirely.
- case_110 (findings): detected Currency Mismatch but not Invalid Currency
  (the EUR invoice itself) — partial-detection error, recommendation correct.

## Which system failed how — the honest comparison

- The baseline's two errors were **missed evidence** (under-detection),
  including the one financially dangerous error of the whole evaluation.
- The agent's three errors were **over-escalation from one extraction
  defect**, all fail-closed.
- The agent was additionally the only system to fully solve the challenging
  case_111 (both findings exactly).

## Remediation hypothesis (to be measured, not assumed)

Requiring `quantity`/`unit_price` in the line-item schema handed to the model
(the sanitization currently strips `required`, see `src/agent/extraction.py`
`UNSUPPORTED_SCHEMA_KEYS`) should eliminate the false-Math-Error class. The
three affected cases would then be expected to resolve to their ground-truth
recommendations through the unchanged deterministic pipeline — but this is a
prediction for a future measured iteration, not a claimed result.
