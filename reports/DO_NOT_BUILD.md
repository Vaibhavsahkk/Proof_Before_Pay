# DO NOT BUILD — Anti-Scope Recommendations

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Purpose:** Features that would add complexity without adding measurable, judge-verifiable evidence for this hackathon. Each recommendation is tied to the project's goals and governance decisions. Nothing here was implemented, and nothing here should be implemented before submission without a new approved decision.

## Standing rule (from the repository's own governance)

`PLAN.md` Phase 3: "Every advanced capability maps to an observed failure or explicit requirement. No complexity is added 'because it sounds agentic.'" `DECISIONS.md` Decision 004: "Start with one primary agent plus deterministic tools. Add extra agents only when an observed failure requires them."

## Do NOT build

| # | Feature | Why it tempts | Why it hurts the evidence | Decision |
| --- | --- | --- | --- | --- |
| 1 | Multi-agent swarm (planner/critic/negotiator agents) | "Agentic workflows" branding | No observed failure in the repository requires a second agent (Decision 004). Adds nondeterminism, cost, and trace complexity that no current metric measures. | Rejected. Revisit only with an observed, documented failure that one agent cannot solve. |
| 2 | Chatbot / conversational interface | Feels like "an AI product" | Target user (AP reviewer) needs an evidence-linked review panel with a deterministic output contract, not free-form dialogue. Chat increases hallucination surface and is unmeasurable by the benchmark. | Rejected. The reviewer UI + CLI + REST API already cover the workflow. |
| 3 | Fake planning UI (animated plan graphs, thinking bubbles) | Demo polish | The real stage-by-stage trace already exists and is more credible. Decorative animation is evidence-free theater. | Rejected. Show the actual JSONL trace and the 4-stage progress checklist instead. |
| 4 | Meaningless memory (general episodic logs, chat history) | "Memory" is a rubric buzzword | Memory must stay evidence-backed and benchmark-anchored: vendor aliases and prior-payment history feed duplicate-billing detection (`src/agent/memory.py`, `tests/test_phase5_memory.py`). Unbounded memory adds leakage and hallucination risk with no metric. | Constrain memory to vendor-alias + prior-history records that a rule consumes. Nothing else. |
| 5 | Vector database / RAG pipeline | "Modern agentic stack" | Evidence bundles are 4-6 small documents; exact retrieval is trivial. A vector store adds dependencies, latency, and approximate-match behavior in a system whose rulebook demands EXACT string equality. | Rejected. Exact-match tooling is the point (`src/tools/equality.py`). |
| 6 | Payment execution / bank-detail mutation | "End-to-end automation" story | Hard project boundary: `docs/LOCKED_PROBLEM.md` and `PLAN.md` Phase 5 explicitly forbid it. It would invalidate the safety story that is core to the evidence. | Forbidden by locked decision. Never build. |
| 7 | Decorative agent animations / progress theatrics in the UI | Perceived sophistication | The UI already passed the usability audit (`reports/phase_4_13_*`, untracked) with a 4-stage real progress checklist. Fake motion undermines trust. | Rejected. |
| 8 | Duplicate business logic (rules re-implemented in UI or LLM prompts) | Convenience / prompt "help" | Business rules live in exactly one place (`src/tools/rule_evaluator.py` + `benchmark/RULEBOOK.md`). Duplication risks silent divergence between what is shown and what is scored. | Rejected. Single source of truth only. |
| 9 | Model fine-tuning / custom models | "Differentiation" | Cost is already honestly UNKNOWN; the frozen benchmark is too small to train on; no metric measures model choice. | Rejected. |
| 10 | Real ERP / bank / accounting integrations | "Production readiness" impression | Explicitly out of scope in `DECISIONS.md` Decision 001 until the core benchmark is proven; deployment is listed UNVERIFIED in `reports/phase_3_7_final_readiness.md` §16. | Rejected for this hackathon. |
| 11 | Multi-tenant cloud deployment, auth, billing | Scale story | Adds attack surface and unverifiable claims. The submission contract is: public repo + reproduction guide + video + trajectories. | Rejected. |
| 12 | Benchmark case padding beyond taxonomy coverage | Inflating apparent rigor or nudging deltas | `docs/PHASE_2_COVERAGE_MATRIX.md` mandates outcome-independent, taxonomy-gap-driven expansion. Adding cases to move a score is outcome-targeting, which the remediation plan explicitly forbids. | Rejected. Expansion stays coverage-driven. |
| 13 | A "verification loop" demo before it is actually implemented | Shows self-correcting agent behavior | A verification-loop result does not exist. Building or simulating one for the video would be a fabricated result. | DO NOT BUILD OR DEMO until implemented and measured; if never implemented, it must never appear in evidence. |

## What TO invest in instead (evidence-positive work)

1. Commit the untracked verified features (failover, document adapter, memory, UI, their tests) so the submitted repository actually contains them.
2. Populate `trajectories/sanitized/` with a small, reviewed set of real sanitized trajectories (see `reports/REPRESENTATIVE_TRAJECTORIES_PLAN.md`).
3. Reconcile documentation to one authoritative status (see `reports/DOCUMENTATION_CONSISTENCY_AUDIT.md`).
4. Complete Track-B phases A1-A5 under their own governance (other agent) so a real measured delta can replace every PENDING marker.
