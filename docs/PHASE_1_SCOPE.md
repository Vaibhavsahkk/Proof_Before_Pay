# PHASE 1 SCOPE: Evidence-Driven Pre-Payment Exception Investigator

## Primary User
Small-business finance/AP reviewer or owner who must review a supplier invoice before payment.

## Workflow Boundary
The investigator agent receives a bundle of evidence. It reasons over the evidence, calls deterministic verification tools, and produces a final recommendation (PAY / HOLD / INVESTIGATE) along with linked findings. The human remains the final decision maker.

## Supported Evidence Types
1. Supplier Invoice
2. Purchase Order
3. Goods Receipt (or delivery record)
4. Vendor Master Record
5. Optional Prior-Payment History
6. Optional Payment/Bank-Change Evidence

## Non-Goals & Safety Boundaries
- **DO NOT** execute a payment.
- **DO NOT** change real bank details.
- **DO NOT** declare a supplier as definitely fraudulent (use evidence-based exception names).
- **DO NOT** send external payment instructions.
- **DO NOT** use private real-world financial data in the repository.
- PAY / HOLD / INVESTIGATE are recommendations only; the human is the final authority.
