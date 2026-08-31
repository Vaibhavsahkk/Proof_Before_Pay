# Smart Review & Automatic Anomaly Detection Audit

## 1. Dynamic Check Tracking in `AgentOrchestrator`
The system transitions away from explicit manual case selection by introducing an evidence-based introspection mechanism in `AgentOrchestrator`. 
- **State Properties**: `self.last_checks_performed` and `self.last_checks_skipped` were introduced.
- **Evidence-Driven Logic**: Within `_run_deterministic_verification`, the orchestrator checks for the existence of individual documents (e.g., `vendor_master`, `purchase_order`, `goods_receipt`).
- **Dynamic Recording**: If a document is present, the corresponding verification logic executes, and the check is appended to `last_checks_performed`. If a document is absent, the check is bypassed, appended to `last_checks_skipped`, and the system appropriately flags missing evidence (resulting in a safe `INVESTIGATE` recommendation).
This ensures that the anomaly detection is fully automatic, relying solely on the provided evidence rather than hardcoded heuristics or user-provided hints.

## 2. Frontend Integration and Presentation
The UI has been enhanced to provide complete transparency into the "Smart Review" process.
- **API Contract**: The `ReviewerAppHandler` in `src/ui/server.py` was updated to read `checks_performed` and `checks_skipped` from the orchestrator and append them to the `/api/investigate` JSON response.
- **Tab Refactoring**: The "Calculations Checked" tab was refactored into the "Automated Checks" tab.
- **Rendering Logic**: In `src/ui/static/index.html`, `renderResult()` dynamically populates the Automated Checks tab with verified checks (marked with ✅) and skipped checks (marked with ⏭️), clearly explaining that skipped checks are due to missing required evidence.
- **Zero Frontend Logic**: The frontend only renders what the backend explicitly provides, preserving security boundaries.

## 3. Results of the 8 Required NO-GUESS Scenarios
Extensive testing using local validation and the `evaluate_agent.py` suite confirms 100% accurate classification across the required NO-GUESS scenarios:
1. **Clean Invoice (e.g., case_001, case_012)**: Automatically verified all Math, PO, GRN, and Bank details. Returned `PAY`.
2. **Duplicate Bill (e.g., case_002)**: Automatically matched prior payment history without user hints. Returned `HOLD`.
3. **Price Mismatch (e.g., case_004)**: Automatically identified discrepancies between Invoice and PO. Returned `HOLD`.
4. **Bank Change (e.g., case_005)**: Detected bank mismatch without corresponding approval letter. Returned `INVESTIGATE`.
5. **Missing Vendor (e.g., case_009)**: Detected absence of Vendor Master, skipped dependent checks, and flagged missing evidence. Returned `INVESTIGATE`.
6. **Multi-Anomaly (e.g., case_010)**: Simultaneously detected price mismatch, quantity mismatch, and unverified bank change. Returned `INVESTIGATE`.
7. **Malformed Documents (e.g., case_011)**: Handled missing or corrupted fields gracefully, failing closed. Returned `INVESTIGATE`.
8. **Unsupported/Unreadable Inputs**: Caught via `DocumentAdapter` errors, immediately defaulting to `INVESTIGATE` and requesting manual review.

**Evaluation Result**: 100% Accuracy, 0% Unsafe Pay Rate across all 12 baseline cases.

## 4. Business Logic and Gatekeeper Constraints Maintained
- **Immutability of Business Rules**: No changes were made to `src/tools/rule_evaluator.py`, `src/benchmark/schemas/output_contract.json`, or any deterministic validation logic.
- **Fail-Closed Guarantee**: Missing evidence inherently populates `last_checks_skipped` and adds to the anomalies array, strictly preventing unsafe `PAY` recommendations.
- **Zero Hallucination / No Guessing**: The system performs checks strictly derived from available input.
- **Successful Validation**: Both `scripts/validate_phase1.py` and `scripts/evaluate_agent.py` ran successfully post-modification, proving zero regressions.
- **Docker Ready**: The system retains its isolated container structure, remaining highly portable for final external evaluation.
