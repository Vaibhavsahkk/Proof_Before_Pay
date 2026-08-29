# Phase 2 Metric Amendment Proposal
**PROPOSAL ONLY - NO CHANGE EFFECTIVE WITHOUT EXTERNAL APPROVAL**

## 1. Context
Phase 2 received a `PHASE FAIL` because the baseline achieved 100% on Exact Case-Level Recommendation Accuracy, the sole primary metric, leaving no measurable headroom for agentic improvement. Expanding the benchmark via a coverage matrix is one remediation path. Amending the metrics to measure more nuanced agent behavior is another complementary path. This document proposes fair, predeclared secondary metrics to evaluate agent quality beyond the final binary recommendation.

## 2. Proposed Secondary Metrics

### 2.1 Evidence Citation / Attribution Correctness
* **Definition:** Measures whether the agent accurately cites the specific documents and values that led to its findings.
* **Formula:** `Sum of correctly cited documents and fields / Total required citations across all ground-truth findings`.
* **Denominator:** Total expected citations across all test cases (e.g., if a finding requires citing an Invoice and a PO, that is 2 required citations).
* **Deterministic Evaluator Feasibility:** High. The ground truth can specify required evidence arrays for each finding. The evaluator checks if the agent's output array includes the exact strings.

### 2.2 Finding Completeness
* **Definition:** Measures whether the agent identified *all* anomalies present in the case, even if it reached the correct final recommendation based on only one of them.
* **Formula:** `Total expected findings correctly identified / Total expected findings across all test cases`.
* **Denominator:** Sum of all expected anomalies (from `RULEBOOK.md` taxonomy) across the benchmark.
* **Deterministic Evaluator Feasibility:** High. Evaluator does a set intersection of agent findings and ground truth findings.

### 2.3 Deterministic-Calculation Correctness
* **Definition:** Verifies the mathematical accuracy of numerical values extracted and computed by the agent (e.g., extracting subtotal, tax, and verifying the math).
* **Formula:** `Cases with 100% correct calculations / Total cases requiring calculations`.
* **Denominator:** Number of cases where calculation verification is applicable.
* **Deterministic Evaluator Feasibility:** High. Evaluator extracts numeric output fields and checks them against ground truth with strict `<= 0.01` tolerance.

### 2.4 Calibrated Escalation
* **Definition:** Evaluates whether an agent unnecessarily escalates safe cases or correctly routes uncertain cases without over-relying on `HOLD`.
* **Formula:**
  * Over-escalation rate = `(Expected PAY but recommended HOLD or INVESTIGATE) / Total Expected PAY cases`
  * Under-escalation rate = `(Expected HOLD but recommended INVESTIGATE) / Total Expected HOLD cases`
* **Aggregation:** Reported as specific error rates to provide diagnostic visibility into agent confidence.

### 2.5 Unsafe-PAY Rate (Existing Guardrail -> Promoted Metric)
* **Definition:** The percentage of `HOLD` or `INVESTIGATE` cases incorrectly recommended as `PAY`.
* **Formula:** `Cases recommended PAY when expected HOLD or INVESTIGATE / Total expected HOLD or INVESTIGATE cases`.
* **Denominator:** Total anomaly-containing cases.
* **Deterministic Evaluator Feasibility:** High. Already implemented as a guardrail.

## 3. Ceiling and Tie Handling
If multiple models achieve 100% on the primary metric (Exact Recommendation Accuracy):
1. **First Tie-Breaker:** Finding Completeness (Reward exhaustive analysis).
2. **Second Tie-Breaker:** Unsafe-PAY Rate (Penalty for critical false negatives).
3. **Third Tie-Breaker:** Cost and Token Efficiency (Reward optimized execution).

If a ceiling persists across all metrics, the benchmark is deemed solved, and new complexity (e.g., larger multi-document bundles) must be introduced in a future phase.

## 4. Anti-Overfitting Safeguards
* **No Retroactive Weighting:** All formulas and denominators must be locked into the evaluator script before the agent baseline is re-run.
* **Strict Evaluation:** Partial credit is never awarded for fuzzy matches. Citations must match exact document IDs, and calculations must match exact decimal values (scale 2, `ROUND_HALF_UP`).
* **Hidden Ground Truth:** Agents are strictly denied access to the `data/cases/ground_truth/` directory during execution. Metrics are computed by the isolated `phase1_verifier` Docker container.

## 5. Review Requirement
This proposal awaits local review and subsequent External ChatGPT authorization before any metric logic in `scripts/validate_phase1.py` or `eval/evaluate_baseline.py` is altered.
