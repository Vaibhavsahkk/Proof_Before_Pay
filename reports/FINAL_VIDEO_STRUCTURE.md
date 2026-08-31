# FINAL VIDEO STRUCTURE — Evidence-First 5-Minute Story

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Hard rule:** This structure makes NO claim of a score that has not been measured. The baseline-vs-agent segment (4:10-4:45) contains only the COMMITTED, frozen-benchmark numbers and explicitly labels the Track-B improvement comparison as **PENDING ACTUAL A5 RESULTS**. Every on-screen number must be traceable to a repository artifact; suggested on-screen citations are given per segment.

## Production notes (before recording)

- Record at the FINAL committed HEAD (after untracked features are committed — see audit §3.1), so what the judge sees matches what they clone.
- Rehearse against the actual commands; use a clean terminal; keep `.env` invisible; never paste keys on screen.
- Have `reports/parallel_submission_evidence_audit.md` open to back any number you say aloud.
- Backup plan if live API quota fails mid-demo: show the committed Phase 3.7 results JSON and a pre-recorded failover clip, and SAY it is pre-recorded. Never disguise it as live.

## Timeline

### 0:00-0:40 — Problem + small-business user
- Hook (plain English): "Before a small business pays a supplier invoice, someone has to check it against the purchase order, the delivery receipt, and the vendor record — across four or five documents, every time. Miss one, and you pay a duplicate bill — or a fraudster's new bank account."
- Show the target user: AP clerk / shop owner with a stack of invoices (per `docs/LOCKED_PROBLEM.md`).
- State the safety boundary up front: the system recommends PAY / HOLD / INVESTIGATE; it never pays. A human decides every time.
- **On-screen evidence:** `docs/LOCKED_PROBLEM.md` (problem statement + hard boundaries).

### 0:40-2:20 — Real Smart Review demo
- Live run 1 — Clean PAY: `python -m src.main --file data/cases/public/case_001.json`. Show the review panel: extracted facts, 4 linked documents, deterministic calculations executed, final `PAY` + human sign-off next step.
- Live run 2 — Multi-finding HOLD: `case_006` (duplicate billing + unverified bank change). Show BOTH findings surfaced (not short-circuited), amber HOLD, escalation to human.
- Live run 3 — Missing evidence INVESTIGATE: `case_011` (missing vendor master). Show checks skipped listed explicitly, missing-evidence flagged, INVESTIGATE with the human next step.
- Optional UI walk (if stable): the reviewer web UI with the same three cases (drag-and-drop intake, 4-stage progress, banners).
- **On-screen evidence:** the CLI output blocks; the JSONL trace file path printed at the end of each run.
- **Say:** "Every number you see was computed by deterministic tools, not the language model."

### 2:20-3:20 — Why this is agentic, and what the LLM does vs deterministic tools
- Architecture in one sentence: LLM = reads messy documents and maps them to a strict schema, then writes the plain-English explanation. Tools = all money math (Python `Decimal`: multiply, sum, tax) and all identity checks (exact string equality). Rules = precedence HOLD > INVESTIGATE > PAY, applied by `RuleEvaluator`.
- Show one real JSONL trace scrolled on screen: `extract -> verify -> apply_rules -> explain -> validate -> escalate`, with the tool names visible.
- Why agentic (say it precisely): the agent DECIDES which checks are possible from the evidence actually present (performs vendor identity check only if vendor master exists; skips and reports otherwise), routes failures (retry on 429 across the credential pool, same-point resume), and fails closed to INVESTIGATE on exhaustion — observed, not asserted.
- **On-screen evidence:** `src/agent/orchestrator.py` stage list; trace file with `deterministic_calculation_references`.


### 3:20-4:10 — Safety / failover / human review
- Failover story (real, observed): show the 429 `RESOURCE_EXHAUSTED` error from a real trace, the masked key slot rotation (`AQ.A...rXsA` -> `AQ.A...6Ikw`), same-stage resume, no data loss. Cite `reports/phase_4_9A_live_recovery_closure.md`.
- Fail-closed: if ALL keys exhaust, output is `INVESTIGATE` with "All credentials exhausted" — show the code path or a controlled test clip (`tests/test_credential_failover.py`). Zero unsafe PAYs is structural, not lucky.
- Human-in-the-loop: every HOLD/INVESTIGATE carries a concrete `required_human_next_step` (e.g., out-of-band callback to a known vendor phone number for bank changes).
- Air-gap: no payment rails exist anywhere in the codebase; ground truth is physically excluded from the runtime image (verifier/runtime Docker separation).
- **On-screen evidence:** trace 429 event; `reports/phase_4_9A_live_recovery_closure.md`; `verify.ps1` forced-failure step.

### 4:10-4:45 — Measured baseline vs agent comparison [ONLY committed numbers; Track-B delta PENDING]
- Say exactly this (all numbers committed and reproducible offline):
  - "On the frozen 12-case benchmark, the fair single-pass baseline — same model, fixed prompt, no tools — scored 100% exact recommendation accuracy. Our agent also scored 100%, with 0 unsafe PAY recommendations out of 10 non-pay cases."
  - "So our honest measured improvement on the primary metric is ZERO on this benchmark. We report that openly. The improvement we DID build — and can show in the trace — is structural: the baseline cannot prove where its evidence came from; our agent cites only documents that are actually present, and every calculation reference is a real tool call, not a hardcoded string."
  - "To get real measurable headroom, we built a second track with messy real-world-style documents." -> **"Track-B baseline vs agent results: PENDING ACTUAL A5 RESULTS — not yet measured, and we won't claim a number until they are."** (If A5 numbers exist by recording time, replace this line with the real measured numbers and their artifact path; otherwise keep the PENDING line verbatim.)
- **On-screen evidence:** `reports/phase_3_7_final_readiness.md` §8 (delta table); `reports/phase_4_evaluation_report.json`; `reports/IMPROVEMENT_CHANGELOG.md`.

### 4:45-5:00 — Biggest learning / hot take
- Deliver the hot take core (from `reports/HOT_TAKE.md`, evidence-backed): "Our biggest failure wasn't the agent — it was the benchmark. The fair baseline scored 100%, leaving us zero measurable headroom. A fair external gate caught it. We fixed the measurement, not the message: we expanded the benchmark along the rulebook taxonomy and are now measuring on messier, more realistic documents."
- Close with the trust principle: "AI reasons over evidence. Deterministic tools calculate. A human decides. And every claim we just made is reproducible from the repo — offline, without an API key."
- **On-screen evidence:** `reports/HOT_TAKE.md`; `BLOCKERS.md` (the PHASE FAIL verdict kept in the repo on purpose).

## Forbidden claims in this video (recording checklist)

- NO percentage improvement on Track-B (PENDING A5).
- NO claim that verification-loop/self-correction exists (NOT IMPLEMENTED).
- NO production/real-data claim (all data is synthetic).
- NO "100% fraud detection" or fraud-labeling language (system never declares a supplier fraudulent).
- NO latency/cost superiority claims (cost UNKNOWN; latency only as measured for the committed baseline run if cited exactly).
- NO claim of macOS/Linux verification (only Windows PowerShell + Git Bash verified).
