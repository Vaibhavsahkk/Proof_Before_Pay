# AI Handoff

## Read These First

1. [[Current Project State]]
2. [[Hackathon Win Dashboard]]
3. [[Project Overview]]
4. [[System Architecture]]
5. [[Known Issues]]
6. [[Decision Log]]
7. [[Important Files]]
8. [[Requirements]]
9. [[Testing and Verification]]
10. [[Phase Roadmap]]

## Project Goal

Build an evidence-driven pre-payment exception investigator for small businesses without performing autonomous execution of payments. The human makes all consequential decisions.

## Current State

Hackathon Phase 1 is APPROVED. Phase 2 is READY FOR EXTERNAL CHATGPT REVIEW. Phase 3+ is locked.

## What Has Been Completed

- Phase 0 Infrastructure and Governance
- Dockerized verification pipelines (`verify.ps1`, `verify.sh`)
- Phase 1 benchmark schemas, data generation, and deterministic ground-truth oracle validation (6 synthetic cases).
- Container isolation and security assertion tests.
- Portable six-case `gemini-3.6-flash` baseline run and deterministic evaluation.
- Exact remote clean-clone verification of the accepted Phase 2 evidence.

## What Is In Progress

- External ChatGPT review of `reports/phase_2_review_packet.md`.

## What Is Not Complete

- Phase 3 through Phase 10 are unstarted/locked. No agent logic exists yet.

## Known Problems

- No known validation failure in Phase 2 candidate `1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c`.
- External approval for Phase 1 has been received.
- Native macOS/Linux execution remains unverified. Git Bash on Windows is the verified POSIX-like environment.

## Important Decisions

- See [[Decision Log]]. Strict adherence to a deterministic evaluation pipeline and fail-closed security assertions. Ground truth files must not be leaked into the agent runtime container.

## Important Constraints

- No payment is ever executed.
- No bank details are changed.
- No supplier is declared definitely fraudulent.
- The human makes all consequential decisions.
- Do not skip tests or fake results.
- Phase 1 needs no model API.
- The current runtime image is non-root and excludes evaluator/ground-truth artifacts. Read-only and network restrictions are future execution requirements, not current verified properties.

## Files That Matter Most

- `PLAN.md`
- `STATUS.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/LOCKED_PROBLEM.md`
- `benchmark/RULEBOOK.md`
- `eval/EVAL_DESIGN.md`

## Current Task

Stop implementation and request the Phase 2 external gate verdict. DO NOT START Phase 3 until the exact verdict `PHASE APPROVED — 100%` is returned.

## Rules For Future AI Agents

- Read this file first.
- Read Current Project State before modifying anything.
- Do not assume undocumented behavior.
- Verify code before claiming completion.
- Do not undo existing decisions without evidence.
- Update project memory after meaningful changes.
