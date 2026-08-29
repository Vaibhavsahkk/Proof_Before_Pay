# Requirements

## Official Hackathon Requirements

- Solve a specific, meaningful problem for a clearly defined user.
- Use agent capabilities purposefully; component count is not a scoring goal.
- Compare a reasonable baseline and final solution on the same task and cases.
- Choose a primary user-success metric before evaluation.
- Record meaningful iterations, including removed experiments, in an improvement changelog.
- Keep consequential actions sandboxed or simulated and require human approval.
- Use public, synthetic, or approved anonymous data.
- Keep credentials and private information outside the submission.
- Connect result claims to submitted evidence.
- Provide code and changelog, reproduction guide, a video up to 5 minutes, and representative trajectories for every agent used.

## Locked Product Requirements

- Primary user: small-business finance/AP reviewer or owner.
- Inputs: invoice, PO, goods receipt/delivery record, vendor master, optional prior-payment history, and optional bank-change evidence.
- Output: evidence-linked `PAY`, `HOLD`, or `INVESTIGATE` recommendation for a human reviewer.
- Deterministic tools perform exact financial calculations.
- The prototype never executes payment, changes real bank details, sends payment instructions, declares a supplier definitely fraudulent, or uses private real-world financial data.

## Current Phase Requirement

Phase 2 must preserve the frozen Phase 1 benchmark, run a reasonable simple baseline, record exact provider/model/prompt/settings/raw outputs/runtime/cost where available, and produce reproducible deterministic evaluation evidence. Phase 3 cannot begin without the exact external verdict `PHASE APPROVED — 100%` for Phase 2.

## Evidence

`sources/official_micro1_hackathon.pdf`, `docs/LOCKED_PROBLEM.md`, `docs/PHASE_1_SCOPE.md`, `PLAN.md`.
