# Project Overview

## Project Name
Proof Before Pay (micro1 Agentic Workflows Hackathon 2026)

## Purpose
Build an evidence-driven pre-payment exception investigator for small businesses. The system will gather and reconcile evidence from supplier invoices, purchase orders, goods receipt records, and vendor master records. It produces an evidence-linked PAY / HOLD / INVESTIGATE recommendation for a human reviewer.

## Current State
Phase 0 (Environment & Governance) is fully completed and verified.
Phase 1 (Problem Scope & Benchmark Design) is implemented and READY FOR EXTERNAL CHATGPT REVIEW, but not approved.
Phases 2 through 10 are completely unstarted and remain LOCKED pending explicit approval from the External ChatGPT gatekeeper.

## Source of Truth
Use the hierarchy in `docs/SOURCE_OF_TRUTH.md`: official hackathon PDF first, original candidate pool second, locked project decision third, then `STATUS.md` plus executable repository artifacts. `PLAN.md` defines phase gates. Advisory research cannot override this hierarchy.

## Key Boundaries
- No payment is ever executed.
- No bank details are changed.
- No supplier is declared definitely fraudulent.
- The human makes all consequential decisions.

## Benchmark Design
The Phase 1 benchmark consists of 6 synthetic cases (`case_001` to `case_006`) covering deterministic exceptions including Duplicate Billing, Quantity Mismatch, Price Contradiction, and Unverified Bank Change. The runtime image excludes ground truth and evaluator artifacts. The separate verifier image contains them for offline validation.
