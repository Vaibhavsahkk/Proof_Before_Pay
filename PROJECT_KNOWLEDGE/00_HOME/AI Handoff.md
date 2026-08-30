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

Hackathon Phase 1 and Phase 2 are APPROVED. Phase 3.1, 3.2, 3.3, and 3.4 are COMPLETE. Phase 3.5 (Agent Optimization) is authorized. Phase 4+ is locked.

## What Has Been Completed

- Phase 0 Infrastructure and Governance
- Dockerized verification pipelines (`verify.ps1`, `verify.sh`)
- Phase 1 benchmark schemas, data generation, and deterministic ground-truth oracle validation.
- Phase 2 baseline script implementation, 12-case expansion, and evaluation.
- Phase 3.1 Baseline Failure Analysis and Phase 3.2 Architecture Requirements.
- Phase 3.3 Agentic Orchestrator and minimum viable deterministic tools implementation, supported by unit tests.

## What Is In Progress

- Formal verification of Phase 3.3 implementation prior to Gate Review.

## What Is Not Complete

- Phase 3.5 (Agent Optimization & Mock Integration) is pending. Phase 4 through Phase 10 are unstarted/locked. Formal agentic scoring has not yet occurred.

## Known Problems

- Hackathon environment API rate limits (`429 RESOURCE_EXHAUSTED`) on free tier restrict full batch processing; system correctly handles this by failing closed to `INVESTIGATE`.
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

Execute Phase 3.5 to optimize the agent and resolve free-tier rate limitations via mock/cached integration. DO NOT START Phase 4 until Phase 3 is fully finalized.

## Rules For Future AI Agents

- Read this file first.
- Read Current Project State before modifying anything.
- Do not assume undocumented behavior.
- Verify code before claiming completion.
- Do not undo existing decisions without evidence.
- Update project memory after meaningful changes.
