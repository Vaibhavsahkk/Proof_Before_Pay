# Phase 3.1 Baseline Failure Analysis

## 1. Objective
Analyze the existing 12-case baseline execution to determine where the baseline succeeds, where it fails or is fragile, and the specific reasoning capabilities required for an agent. Identify the boundary between deterministic solutions and agentic orchestration, and define metric opportunities for Phase 3.

## 2. Baseline Run Identity
- **Run ID:** `run_20260830_091031_f1cc354c`
- **Model:** `gemini-3.6-flash`
- **Cases Evaluated:** 12

## 3. Reconstructed Baseline Results

| CASE | BASELINE RECOMMENDATION | EXPECTED RECOMMENDATION | FINDINGS | EXPECTED FINDINGS | SCHEMA STATUS | LATENCY | NOTABLE BEHAVIOR |
|---|---|---|---|---|---|---|---|
| case_001 | PAY | PAY | None | None | VALID | 10.15s | Perfect match |
| case_002 | HOLD | HOLD | Duplicate Billing | Duplicate Billing | VALID | 10.19s | Perfect match |
| case_003 | HOLD | HOLD | Quantity Mismatch | Quantity Mismatch | VALID | 6.42s | Perfect match |
| case_004 | HOLD | HOLD | Price Contradiction | Price Contradiction | VALID | 14.45s | Perfect match |
| case_005 | INVESTIGATE | INVESTIGATE | Unverified Bank Change | Unverified Bank Change | VALID | 8.59s | Perfect match |
| case_006 | HOLD | HOLD | Duplicate Billing, Unverified Bank Change | Duplicate Billing, Unverified Bank Change | VALID | 16.58s | Perfect match |
| case_007 | HOLD | HOLD | Math Error | Math Error | VALID | 7.66s | Perfect match |
| case_008 | HOLD | HOLD | Currency Mismatch, Invalid Currency | Currency Mismatch, Invalid Currency | VALID | 8.15s | Perfect match |
| case_009 | INVESTIGATE | INVESTIGATE | Vendor Identity Mismatch | Vendor Identity Mismatch | VALID | 11.20s | Perfect match |
| case_010 | INVESTIGATE | INVESTIGATE | Missing PO Line ID | Missing PO Line ID | VALID | 9.76s | Perfect match |
| case_011 | INVESTIGATE | INVESTIGATE | Missing Vendor Master | Missing Vendor Master | VALID | 6.76s | Perfect match |
| case_012 | PAY | PAY | None | None | VALID | 11.26s | Perfect match |

## 4. Primary Metric Analysis
- **Exact Case-Level Recommendation Accuracy:** 100.0%
- **Unsafe-PAY Rate:** 0.0%
- **Schema Validity:** 100.0%
- **Findings Correctness:** 100.0%
- **Latency (Mean):** 10.10s
- **Token Usage:** 23314 Prompt / 3095 Candidates

## 5. Observed Failures
**NO OBSERVED OUTPUT FAILURE IN THIS RUN.**
The baseline model correctly identified every case, returned 100% valid schema outputs, and properly executed all required findings based on the provided single-pass prompt.

## 6. Deep Failure / Weakness Analysis & Latent Weaknesses
Because there are NO OBSERVED OUTPUT FAILURES, we look at the latent risks associated with a single-pass LLM baseline, based on rulebook complexity and multi-signal reasoning:

- **Case 007 (Math Error):** *Correct but fragile (Latent Risk).* Relying on a language model to perform exact decimal arithmetic for `ROUND_HALF_UP` and strict `0.01` tolerance is highly fragile in production. Single-pass LLMs are prone to hallucinating math over long contexts.
- **Case 006 (Duplicate Billing & Bank Change):** *Correct but fragile (Latent Risk).* Requires cross-checking multiple documents simultaneously (prior history, vendor master, invoice, bank evidence). A monolithic prompt becomes fragile when the document bundle scales.
- **Case 008 (Currency Mismatch):** *Correct and robust.* Simple string matching is well within LLM capabilities.
- **Case 009 (Vendor Identity Mismatch):** *Correct but fragile (Latent Risk).* Real-world vendor names might have fuzzy differences (e.g., "Inc" vs "Inc."). The rulebook strictly requires "exact match." Relying purely on an LLM for deterministic string equality is risky.

## 7. Case-by-Case Reasoning Demand
1. **case_001 (PAY):** Evidence attribution, baseline arithmetic verification.
2. **case_002 (HOLD - Duplicate):** Cross-document comparison (History vs Invoice), identity resolution, quantity/price matching.
3. **case_003 (HOLD - Qty Mismatch):** Quantity reconciliation across Invoice and GRN.
4. **case_004 (HOLD - Price Contradiction):** Price reconciliation across Invoice and PO.
5. **case_005 (INVESTIGATE - Bank Change):** Multi-signal precedence, conditional logic (checking approval status and old/new accounts).
6. **case_006 (HOLD - Multi-Finding):** Simultaneous cross-document comparison, history lookup, multi-signal precedence (Bank + Duplicate).
7. **case_007 (HOLD - Math Error):** Arithmetic verification, exact tolerance checking.
8. **case_008 (HOLD - Currency):** Currency comparison, strict rule validation.
9. **case_009 (INVESTIGATE - Identity):** Identity resolution, exact equality matching.
10. **case_010 (INVESTIGATE - Missing PO Line):** Missing-object handling, cross-document item mapping.
11. **case_011 (INVESTIGATE - Missing Vendor):** Missing-object handling.
12. **case_012 (PAY):** Multi-signal consolidation, comprehensive evidence check.

## 8. Deterministic-Tool Opportunities
These tasks should NOT be left purely to LLM reasoning due to hallucinations and exactness requirements:
- **Exact Decimal Arithmetic:** (Calculation of subtotals, tax, tolerances). 
- **Exact String Equality:** (Vendor IDs, Item IDs).
- **Schema Validation:** (Checking nulls in `purchase_order` or `vendor_master`).

## 9. Agentic Opportunities
Areas where a multi-step agent adds value over a single prompt:
- **OBSERVE & EXTRACT:** Intelligently scanning unstructured elements and extracting them for tools.
- **VERIFY (Evidence Attribution):** Locating specific line numbers, document IDs, or paragraphs to ground decisions.
- **EXPLAIN & ESCALATE:** Providing calibrated, nuanced reasons for why an investigation is required without triggering false alarms.
- **Dynamic Routing:** Deciding *which* tool to call based on the document type, reducing token overhead.

## 10. Metric Implications
Since Exact Recommendation Accuracy is at 100%, we must adopt the secondary metrics from the Phase 2 Amendment Proposal:
- **Evidence Citation / Attribution Correctness:** Will expose whether the baseline actually "knows" where the data came from, or if it guessed correctly.
- **Deterministic-Calculation Correctness:** Will strictly punish LLM math hallucinations if evaluated with strict numerical tolerance.
- **Finding Completeness:** Ensures an agent finds *all* overlapping issues (like Case 006) rather than just short-circuiting on the first HOLD.

## 11. Baseline Weakness Map

| CAPABILITY | BASELINE BEHAVIOR | OBSERVED EVIDENCE | RISK | FUTURE AGENT OPPORTUNITY | DETERMINISTIC TOOL OPPORTUNITY | METRIC THAT MEASURES IT |
|---|---|---|---|---|---|---|
| Arithmetic Verification | Single-pass prompt | Success in case_007 | Math hallucination | Extract values, pass to tool | Calculator tool (strict 0.01 tolerance) | Deterministic-Calculation Correctness |
| Cross-Doc Matching | Single-pass prompt | Success in case_002, 004 | Context window confusion | Dynamic querying of docs | Exact-match ID comparison tool | Evidence Citation Correctness |
| Evidence Attribution | Inline generation | References produced | Hallucinated citations | Explicit grounding requirement | Tool output parser | Evidence Citation Correctness |
| Multi-Anomaly Detection | Single-pass prompt | Success in case_006 | Short-circuiting early | Iterative checklist loop | Aggregation logic | Finding Completeness |

## 12. Agent Necessity Test
- **Could a deterministic program solve this completely?** YES, for the highly structured JSON data currently in the benchmark, a pure Python script could achieve 100% without an LLM.
- **Why use an Agent?** The real-world problem involves semi-structured or unstructured text where schemas vary. The LLM is necessary for semantic mapping (EXTRACT), while deterministic tools are necessary for execution (CALCULATE, EXACT MATCH). The division of labor is: LLM for understanding and extraction, Tools for math and strict logic.

## 13. Competitive Hypothesis
To demonstrate meaningful agentic improvement, our future system must achieve:
- **Better evidence attribution:** Provably tracing every calculation and comparison back to specific document fields without hallucination.
- **Deterministic correctness:** Offloading math to a strict tool to guarantee zero arithmetic hallucinations.
- **Scalable architecture:** A pattern that works regardless of context window length by selectively querying tools, rather than dumping all documents into one prompt.

## 14. Commands Run
- `python scratch_table.py` to reconstruct evaluation results.
- `cat evaluation_report.json` (via agent tool)

## 15. Actual Outputs
Refer to Section 3.

## 16. Unverified Items
- Whether the baseline hallucinated evidence citations. (Latent hypothesis, needs measurement).

## 17. Human Action Required
None.

## 18. Phase 3.2 Recommendation
Phase 3.1 analysis complete. The baseline ceiling (100%) requires adopting the secondary metrics (Phase 2 Amendment Proposal) and building a hybrid agent architecture (LLM + Deterministic Tools) to prove robustness against latent risks like math and attribution hallucination.
PROCEED to Phase 3.2 (Agent Architecture Design).

## 19. Phase 3.1 Status
**READY FOR PHASE 3.1 GATE REVIEW**
