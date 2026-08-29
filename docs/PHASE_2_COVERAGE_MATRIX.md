# Phase 2 Coverage Matrix & Expansion Proposal

## 1. Context & Purpose
Following the Phase 2 (Fair Baseline) `PHASE FAIL` verdict, the baseline achieved 100% Exact Case-Level Recommendation Accuracy on the frozen 6-case benchmark. To establish a rigorous, measurable foundation for agentic improvement without outcome-targeting, this document maps the current benchmark coverage against the authoritative taxonomy in `benchmark/RULEBOOK.md`. 

The objective is to identify legitimate, untested workflow gaps and anomaly types to justify expanding the benchmark to 12 cases. 

## 2. Current Benchmark Coverage (Cases 001 - 006)

| Case ID | Expected Outcome | Anomalies Present | Taxonomy Category | Coverage Status |
|---------|-----------------|-------------------|-------------------|-----------------|
| `case_001` | PAY | None | PAY | Covered |
| `case_002` | HOLD | Duplicate Billing | HOLD | Covered |
| `case_003` | HOLD | Quantity Mismatch | HOLD | Covered |
| `case_004` | HOLD | Price Contradiction | HOLD | Covered |
| `case_005` | INVESTIGATE | Unverified Bank Change | INVESTIGATE | Covered |
| `case_006` | HOLD | Duplicate Billing, Unverified Bank Change | HOLD, INVESTIGATE | Covered (Precedence Test) |

**Analysis of Current Coverage:**
The current 6 cases cover the basic execution paths (clean PAY, single HOLD, single INVESTIGATE) and one multi-signal precedence test. However, large portions of the `RULEBOOK.md` anomaly taxonomy remain completely untested.

## 3. Identified Coverage Gaps

Based on `benchmark/RULEBOOK.md`, the following critical anomaly types are currently **untested**:

### Untested HOLD Conditions:
1. **Currency Mismatch** (Invoice vs PO)
2. **Invalid Currency** (Not exactly USD)
3. **Tax Rate Contradiction**
4. **Math Errors** (Line total calculations, subtotal summation, tax calculation, or grand total calculation)

### Untested INVESTIGATE Conditions:
1. **Missing Vendor Master** (Object is null)
2. **Vendor Identity Mismatch** (Name or Tax ID mismatch)
3. **Missing PO / Missing GRN** (Objects are null)
4. **Duplicate Line ID** 
5. **Missing PO Line ID / Missing GRN Line ID** (Orphaned invoice lines)

### Untested Workflow Complexities:
1. **Verified Bank Change (PAY)**: The rulebook states an `Unverified Bank Change` is an INVESTIGATE condition *unless* it is verified via a matching `old_bank_account`, `new_bank_account`, and `APPROVED` status. An invoice with a valid, approved bank change should result in a `PAY` recommendation. This is currently untested.

## 4. Proposed Expansion Cases (Cases 007 - 012)

To address these gaps without forcing outcome bias, we propose 6 new frozen cases carefully designed to test the absent taxonomy items:

| Proposed ID | Target Outcome | Primary Anomaly Focus | Justification |
|-------------|---------------|-----------------------|---------------|
| `case_007` | HOLD | Math Error (Sum of line totals != subtotal) | Tests deterministic decimal calculation logic. |
| `case_008` | HOLD | Currency Mismatch (Invoice vs PO) | Tests explicit string comparison constraints. |
| `case_009` | INVESTIGATE | Vendor Identity Mismatch | Tests master data validation. |
| `case_010` | INVESTIGATE | Missing PO Line ID | Tests line-item level cross-document reconciliation. |
| `case_011` | PAY | Verified Bank Change (Approved) | Tests complex conditional exemptions (Exception to INVESTIGATE). |
| `case_012` | HOLD | Math Error + Missing GRN (Multi-signal) | Tests complex precedence (HOLD > INVESTIGATE) across missing objects and math. |

## 5. Next Steps for Remediation
1. **Review & Approval:** This coverage matrix must be reviewed and approved (conceptually by the user/gatekeeper) to confirm it does not violate the anti-overfitting rules.
2. **Drafting Cases:** Once approved, cases `007` through `012` will be authored adhering strictly to the `benchmark/schemas/` JSON definitions.
3. **Ground Truth Validation:** The ground truth files for `007`-`012` will be created and visually verified for strict `RULEBOOK.md` compliance.
4. **Test Suite Updates:** `scripts/validate_phase1.py` and Pytest harnesses will be updated to accommodate 12 cases.
5. **Baseline Execution:** The Phase 2 baseline will be re-run on all 12 cases. The resulting accuracy metric will be recorded as the new official baseline, regardless of whether it is 100% or lower.
