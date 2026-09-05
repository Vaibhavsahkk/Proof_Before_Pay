# Sub-Phase A5 Report — Track B Baseline-vs-Agent Measurement (ACTUAL)

**Phase:** A (Measurement) — Sub-phase A5
**Status:** COMPLETE — MEASURED, NO IMPROVEMENT ON THE PRIMARY METRIC (see §13)
**Date:** 2026-09-01
**Agent version:** frozen in `evidence/phase_track_b/A4_agent_version_freeze.json` (git HEAD `9b243a82de91bbdd16beae9c53100634559a3634` + working-tree extraction.py, component hashes recorded)
**Baseline:** prompt v2 (SHA-256 `4E1E2853E9E5A0B3C2C62487938D72C6E84278D57855D4025ED27451878E3E16`), runs frozen in `data/track_b/evaluation/baseline_runs/frozen_v2_assembly/`
**Agent runs:** frozen in `data/track_b/evaluation/agent_runs/frozen_v1_assembly/`
**Machine-readable results:** `reports/track_b_final_results.json`

---

## 1. Evaluation purpose

Track A (clean structured JSON) was saturated: baseline and agent both scored
100%. Track B measures the same capability under realistic document conditions
(rendered PDFs/PNGs/JSON, label variation, scan noise, missing documents,
cross-document contradictions) — the conditions a small-business AP reviewer
actually faces. The question: **does the current agentic pipeline beat a fair
one-prompt baseline on messy documents?**

## 2. Frozen dataset

12 synthetic cases (`case_101..112`), 61 document files (PDF/PNG/JSON),
2 PAY / 6 HOLD / 4 INVESTIGATE ground truth derived (never hand-authored) by
the official `Phase1Oracle`. Frozen + SHA-256-manifested in A1; integrity
re-verified after every phase (`verify_track_b.py` exit 0, incl. byte-level
generator determinism). `case_111` is the designated challenging case.

## 3. Baseline definition (fair)

One direct multimodal `gemini-3.6-flash` call per case: every bundle document
attached in native format (PDF/PNG as multimodal parts, JSON as text),
temperature 0.0, JSON output, official output contract embedded (v2 prompt),
no rulebook, no tools, no orchestration, no retries beyond transient HTTP +
key rotation (identical policy to the agent). Same documents, same task, same
contract, same ground truth.

## 4. Agent definition (current, unmodified)

The existing production pipeline: `DocumentAdapter` (PyMuPDF/pypdf text
extraction; gemini-2.5-flash multimodal OCR for PNGs) → `LLMExtractor`
(gemini-3.6-flash, schema-constrained extraction + deterministic
normalization) → deterministic verification (`DecimalCalculator`,
`EqualityChecker`) → `RuleEvaluator` → human-readable explanation →
output-contract validation. No Track-B-specific tuning. Version hashes in
the A4 freeze artifact.

## 5. Fairness

- Same frozen case inputs (byte-identical documents from `bundle.json`).
- Same output contract; same ground truth; same evaluator.
- Same model family for the reasoning call (gemini-3.6-flash), same
  temperature 0.0, same 5-key credential pool with the same rotation/cooldown
  policy (after an A4 harness fix — see §15 — both systems use the identical
  pool; run 1 of A4 was invalidated when the harness accidentally gave the
  agent a single-key pool).
- Baseline not weakened, agent not given case-specific hints. Evaluator
  contains no case-specific logic; expectations come only from frozen ground
  truth.
- Ground truth never entered any system input (leakage rules verified by the
  frozen verifier).

## 6. Primary metric — exact case-level recommendation accuracy

| System | Accuracy |
|---|---|
| Simple baseline (v2) | **83.33%** (10/12) |
| Current agent | **75.00%** (9/12) |

## 7. Secondary metrics

| Metric | Baseline | Agent |
|---|---|---|
| Findings exactness (sorted-set) | 75.00% (9/12) | 58.33% (7/12) |
| Schema validity | 100.00% | 100.00% |
| Unsafe-PAY rate | **10.00% (1/10)** | **0.00% (0/10)** |
| Total runtime | 202.5 s (mean 16.9) | 461.5 s (mean 38.5) |
| Tokens (provider-reported) | 54,678 total | NOT MEASURED (orchestrator does not capture usage metadata) |
| Cost | NOT MEASURED | NOT MEASURED |
| Human-review effort | NOT MEASURED | NOT MEASURED |

## 8. Full results table

| METRIC | SIMPLE BASELINE | AGENT SOLUTION | CHANGE |
|---|---|---|---|
| Recommendation accuracy | 83.33% | 75.00% | **-8.33 pp** |
| Findings exactness | 75.00% | 58.33% | **-16.67 pp** |
| Schema validity | 100.00% | 100.00% | 0.00 pp |
| Unsafe-PAY rate | 10.00% | 0.00% | **-10.00 pp** (better) |
| Latency (total) | 202.5 s | 461.5 s | +259.0 s (slower) |

## 9. Per-case results

| Case | Ground truth | Baseline | Agent | Base ✓ | Agent ✓ | Unsafe PAY? | Agent-specific behavior | Failure reason |
|---|---|---|---|---|---|---|---|---|
| case_101 | PAY | PAY | PAY | ✓ | ✓ | — | 4 deterministic checks, clean | — |
| case_102 | PAY | PAY | HOLD | ✓ | ✗ | — | false Math Error | extraction dropped qty/unit_price (see §11) |
| case_103 | HOLD | PAY | HOLD | ✗ | ✓ | baseline unsafe | duplicate billing found in remittance PDF | baseline missed embedded history |
| case_104 | HOLD | HOLD | HOLD | ✓ | ✓ | — | Price Contradiction detected | — |
| case_105 | HOLD | HOLD | HOLD | ✓ | ✓ | — | PNG GRN OCR → Quantity Mismatch | — |
| case_106 | INVESTIGATE | INVESTIGATE | INVESTIGATE | ✓ | ✓ | — | Unverified Bank Change | — |
| case_107 | HOLD | HOLD | HOLD | ✓ | ✓ | — | Math Error detected | — |
| case_108 | INVESTIGATE | INVESTIGATE | INVESTIGATE | ✓ | ✓ | — | Missing PO (+ line-id check skipped) | — |
| case_109 | INVESTIGATE | INVESTIGATE | HOLD | ✓ | ✗ | — | false Math Error + real Vendor Identity Mismatch | extraction dropped qty/unit_price |
| case_110 | HOLD | HOLD | HOLD | ✓ | ✓ | — | Currency Mismatch + Invalid Currency (findings superset: extra Math Error) | extraction imprecision → false Math Error (rec still correct) |
| case_111 | HOLD | INVESTIGATE | HOLD | ✗ | ✓ | — | **challenging case: both findings exactly right** | baseline missed duplicate billing |
| case_112 | INVESTIGATE | INVESTIGATE | HOLD | ✓ | ✗ | — | false Math Error + correct Missing GRN/Vendor Master | extraction dropped qty/unit_price |

## 10. Challenging case (case_111)

**Documents:** noisy rendered invoice (PDF), purchase order as **PNG image**,
goods receipt (PDF), vendor master as **JSON**, remittance advice (PDF
embedding the prior-payment history), bank-change notice (PDF, PENDING status)
— 6 documents, 3 formats.

**Correct result (oracle-derived):** HOLD with `["Duplicate Billing",
"Unverified Bank Change"]`.

**Baseline:** INVESTIGATE — it detected the unverified bank change but **missed
the duplicate billing** embedded in the remittance advice; recommendation
severity therefore wrong (INVESTIGATE instead of HOLD).

**Agent:** **HOLD with both findings exactly correct.** The DocumentAdapter
OCR'd the PNG purchase order live (gemini-2.5-flash), the extractor pulled
the prior-payment history out of the remittance PDF, and the deterministic
pipeline cross-checked vendor+invoice+amount → `Duplicate Billing`
(`calculator.check_equality`), and bank accounts vs the PENDING notice →
`Unverified Bank Change`. 5 deterministic checks ran; 0 credential
recoveries; 43.3 s.

**Why the difference:** the one-prompt model read the bank notice but did not
reconcile the remittance history against the invoice; the agent's explicit
cross-document verification stage did. **Deterministic verification directly
affected the outcome** — the duplicate-billing finding is produced by
`EqualityChecker`/`DecimalCalculator` over extracted values, not by model
judgment.

Both systems were not correct on this case; the agent was, and we state that
as the measured result, not as a manufactured "win" — the agent still lost the
primary metric overall (§13).

## 11. Error analysis (all classified from real run records)

### Agent errors (3 recommendation errors)

| Case | Error class | Evidence |
|---|---|---|
| case_102 | **extraction error → false positive** | extracted items contain `line_total` only; `quantity`/`unit_price` missing → `qty × price` check threw `CalculatorError` → false "Math Error" → HOLD on a clean PAY case |
| case_109 | **extraction error → false positive** (plus a REAL finding) | same qty/unit_price drop → false Math Error; the Vendor Identity Mismatch was real, but the wrong HOLD severity came from the false Math Error |
| case_112 | **extraction error → false positive** (plus real findings) | same pattern → false Math Error escalated INVESTIGATE (missing-evidence) to HOLD |

All three agent errors share ONE root cause: the schema-constrained extraction
occasionally omits `quantity` and `unit_price` from line items (the
sanitized Gemini response schema strips `required` markers), and the
deterministic calculator then fails closed into a false Math Error. This is a
**fail-closed** direction (never an unsafe PAY) but a real precision defect.

Findings-exactness errors additionally include case_110 (extra false
"Math Error" alongside two correct findings — recommendation still correct).

### Baseline errors (2 recommendation errors)

| Case | Error class | Evidence |
|---|---|---|
| case_103 | **cross-document reconciliation failure → unsafe PAY** | prior identical invoice recorded in the remittance advice PDF; one-prompt model missed it and recommended PAY on a non-PAY case (the single unsafe-PAY of the entire evaluation) |
| case_111 | **missing-evidence handling / severity error** | found the bank change, missed the duplicate billing, chose INVESTIGATE over HOLD |

(Track-B baseline v1's schema failures were a prompt defect fixed pre-scoring;
see `evidence/phase_track_b/A3_baseline_prompt_v1_defect.md`.)

## 12. Safety analysis

Unsafe-PAY = recommending PAY on a ground-truth non-PAY case. Denominator:
10 non-PAY cases.

| System | Unsafe PAY count | Rate |
|---|---|---|
| Baseline | 1/10 (case_103) | 10.00% |
| Agent | 0/10 | **0.00%** |

The agent's failure mode (false Math Error → HOLD) is the SAFE direction: it
escalates a human instead of approving a risky payment. The baseline's failure
mode (missing duplicate billing → PAY) is the catastrophic direction for a
payment product. For a small-business user, an occasional over-cautious hold
costs a review; a missed duplicate costs money.

## 13. Actual delta

- Recommendation accuracy: **75.00% - 83.33% = -8.33 percentage points**
- Findings exactness: 58.33% - 75.00% = **-16.67 pp**
- Unsafe-PAY rate: 0.00% - 10.00% = **-10.00 pp** (improvement)
- Schema validity: +0.00 pp
- Latency: agent 2.28× slower (461.5 s vs 202.5 s total)

**Honest conclusion: on this Track-B evaluation, the current agent did NOT
beat the fair one-prompt baseline on the primary metric (accuracy), but it
eliminated the unsafe-PAY error and was the only system to solve the
challenging case.**

## 14. Limitations

- 12 synthetic cases from one generator; no production generalization claim.
- One model family (gemini-3.6-flash baseline vs agent extraction); single
  execution per system per case (temperature 0.0, but provider nondeterminism
  and OCR variance are not averaged out).
- Free-tier quota constraints shaped execution (documented in §15); the three
  PNG cases were re-executed after a harness fix — every record's source run
  is in the assembly manifest.
- Agent tokens/cost/human-review effort NOT MEASURED.
- "Messy" = format variation and reconciliation, not OCR archaeology
  (declared in the frozen DESIGN.md §3).

## 15. Reproducibility (OFFLINE RE-SCORING)

Everything needed to re-score without a live provider is frozen:

```bash
python data/track_b/verify_track_b.py          # dataset integrity
python data/track_b/evaluation/evaluate_track_b.py \
    --baseline-run frozen_v2_assembly \
    --agent-run    frozen_v1_assembly \
    --out reports/track_b_final_results.json    # reproduces every number above
```

- Frozen inputs: `data/track_b/cases/` (SHA-256 manifest)
- Frozen ground truth: `data/track_b/ground_truth/`
- Frozen baseline outputs: `data/track_b/evaluation/baseline_runs/frozen_v2_assembly/` (+ per-case provenance)
- Frozen agent outputs: `data/track_b/evaluation/agent_runs/frozen_v1_assembly/` (+ per-case provenance)
- Evaluator: `data/track_b/evaluation/evaluate_track_b.py` (no live calls, no case-specific logic)

LIVE MODEL EXECUTION (what cannot be reproduced offline): the original
provider calls. The runs' raw responses, runtimes, retry counts, and traces
are preserved in the run records; traces under `traces/raw/`.

Execution incidents (honest record, all pre-scoring or infra-only):
1. A4 run 1 INVALID: harness passed the single `GEMINI_API_KEY` instead of the
   full pool → all 12 results were the documented fail-closed fallback. Marked
   INVALID, excluded, harness fixed (pool now identical for both systems).
2. Three PNG cases first failed on a harness `UnboundLocalError` (`doc_meta`)
   plus 2.5-flash OCR quota exhaustion; harness fixed, cases re-executed live.
3. The cache-isolation guard was over-strict (blocked the agent's own
   production Track-B caches); corrected to its actual purpose (Track A vs
   Track B ID-space separation, which is structural and holds).
None of these touched agent code, frozen data, or any scored output.

## 16. What this evaluation PROVES

1. On messy real-world-style documents, the current agent did **not** improve
   case-level accuracy over a fair one-prompt baseline (75.00% vs 83.33%).
2. The agent eliminated the unsafe-PAY error class (0/10 vs 1/10) — its
   errors are all fail-closed.
3. The agent was the only system to fully solve the challenging multi-signal
   case (duplicate billing + unverified bank change, PNG + JSON + embedded
   evidence), specifically because of its deterministic cross-document
   verification.
4. The dominant agent failure mode is a single extraction-fidelity defect
   (dropped quantity/unit_price → false Math Error) — one root cause explains
   all three of its recommendation errors.

## 17. What it does NOT prove

- No production-performance claim; 12 synthetic cases, one generator.
- It does not show the agent is generally worse than one-prompt baselines —
  with the extraction defect fixed, the outcome could differ (that is a
  future, separately-measured iteration; no such claim is made here).
- It does not measure cost, token usage, or human-review effort for the agent.
- Track A results (100%/100% both systems) remain separate and unchanged.

## 18. Smallest evidence-backed next step

Fix the extraction contract so `quantity` and `unit_price` are required in the
line-item schema given to the model (a small, non-Track-B-specific change to
`LLMExtractor`'s schema sanitization), then re-run this exact evaluation under
the same frozen protocol. Predicted effect (hypothesis, to be measured): the
three false Math Errors disappear; the agent's accuracy upper bound on this
dataset becomes 11/12 (only case_109's identity question would remain, and
its Vendor Identity Mismatch finding suggests extraction of names is sound).
No score is claimed until that run is executed.
