# Phase 2 Coverage Matrix & Expansion Proposal

## 1. Context & Purpose
Following the Phase 2 (Fair Baseline) `PHASE FAIL` verdict, the baseline achieved 100% Exact Case-Level Recommendation Accuracy on the frozen 6-case benchmark. To establish a rigorous, measurable foundation for agentic improvement without outcome-targeting, this document maps the current benchmark coverage against the authoritative taxonomy in `benchmark/RULEBOOK.md`. 

The objective is to identify legitimate, untested workflow gaps and anomaly types to justify expanding the benchmark based strictly on taxonomy coverage, avoiding any predetermined or arbitrary case counts.

## 2. Selection Rule for Benchmark Expansion
- **Outcome-Independent:** Case inclusion is determined solely by the presence of unrepresented taxonomy elements, not by the baseline's expected success or failure.
- **Coverage Mandate:** Include one atomic test case for each unrepresented primary rulebook category to ensure baseline algorithms are tested against all deterministic rule variants.
- **Representative Sampling:** For categories with multiple sub-types (e.g., Math Errors have 4 sub-types), sample one representative sub-type to bound dataset size while proving algorithmic capability, unless specific sub-types exercise distinct data sources (e.g., PO vs. GRN).
- **No Artificial Complexity:** Do not artificially combine anomalies unless explicitly testing precedence boundaries.

## 3. Current Benchmark Coverage (Cases 001 - 006)

| Case ID | Rule-derived Expected Recommendation | Anomalies Present | Taxonomy Category | Coverage Status |
|---------|--------------------------------------|-------------------|-------------------|-----------------|
| `case_001` | PAY | None | PAY | Covered |
| `case_002` | HOLD | Duplicate Billing | HOLD | Covered |
| `case_003` | HOLD | Quantity Mismatch | HOLD | Covered |
| `case_004` | HOLD | Price Contradiction | HOLD | Covered |
| `case_005` | INVESTIGATE | Unverified Bank Change | INVESTIGATE | Covered |
| `case_006` | HOLD | Duplicate Billing, Unverified Bank Change | HOLD, INVESTIGATE | Covered (Precedence Test) |

## 4. Taxonomy & Gap Analysis

Based on `benchmark/RULEBOOK.md`, the following maps every approved taxonomy and safety category to existing coverage or identifies it as a gap:

### HOLD Conditions
| Anomaly Type | Coverage | Proposed Resolution |
|--------------|----------|---------------------|
| Duplicate Billing | Covered (`case_002`, `case_006`) | None |
| Quantity Mismatch | Covered (`case_003`) | None |
| Price Contradiction | Covered (`case_004`) | None |
| Currency Mismatch | **Gap** | Draft candidate |
| Invalid Currency | **Gap** | Omitted (Redundant to Currency Mismatch for testing string comparison logic) |
| Tax Rate Contradiction | **Gap** | Omitted (Redundant to Price Contradiction for testing line-item field comparison) |
| Math Error | **Gap** (4 subtypes) | Draft candidate (Sample: Sum of line totals != subtotal) |

### INVESTIGATE Conditions
| Anomaly Type | Coverage | Proposed Resolution |
|--------------|----------|---------------------|
| Missing Vendor Master | **Gap** | Draft candidate |
| Vendor Identity Mismatch | **Gap** | Draft candidate |
| Unverified Bank Change | Covered (`case_005`, `case_006`) | None |
| Missing PO | **Gap** | Draft candidate |
| Missing GRN | **Gap** | Omitted (Redundant to Missing PO for testing missing object handling) |
| Duplicate Line ID | **Gap** | Omitted (Rare structural JSON error, lower priority than reconciliation logic) |
| Missing PO Line ID | **Gap** | Draft candidate |
| Missing GRN Line ID | **Gap** | Omitted (Redundant to Missing PO Line ID) |

### PAY Exceptions / Workflows
| Workflow / Exception | Coverage | Proposed Resolution |
|----------------------|----------|---------------------|
| Clean PAY | Covered (`case_001`) | None |
| Verified Bank Change | **Gap** | Draft candidate (Tests condition where bank change is approved, leading to PAY) |

## 5. Draft Candidate Additions

Derived mechanically from the selection rule and gap analysis. These are draft candidates only and do not mandate an arbitrary final case count.

| Proposed Candidate | Primary Anomaly Focus | Rule-derived Expected Recommendation | Justification |
|--------------------|-----------------------|--------------------------------------|---------------|
| `candidate_A` | Math Error (Sum of line totals != subtotal) | HOLD | Tests deterministic decimal calculation logic. |
| `candidate_B` | Currency Mismatch (Invoice vs PO) | HOLD | Tests explicit string comparison constraints. |
| `candidate_C` | Vendor Identity Mismatch | INVESTIGATE | Tests master data string validation. |
| `candidate_D` | Missing PO Line ID | INVESTIGATE | Tests line-item level cross-document reconciliation. |
| `candidate_E` | Missing Vendor Master | INVESTIGATE | Tests missing root object handling. |
| `candidate_F` | Verified Bank Change (Approved) | PAY | Tests complex conditional exemptions (Exception to INVESTIGATE). |

## 6. Next Steps
1. **Review & Approval:** This coverage matrix must be reviewed and approved locally to confirm it aligns with outcome-independent rules.
2. **Drafting Cases:** Once approved, the draft candidates will be authored adhering strictly to `benchmark/schemas/`.
3. **Metric Amendment:** A separate metric amendment proposal will be reviewed to determine how expanded coverage is scored.
