# AI Operating Contract

## Startup Protocol

Before any material action:

1. Read [[START HERE]].
2. Read [[Current Project State]] and [[AI Handoff]].
3. Read repository `STATUS.md`, `PLAN.md`, `DECISIONS.md`, and `BLOCKERS.md`.
4. Read the relevant source-of-truth files and code.
5. Inspect Git status before editing.
6. Confirm the action is allowed in the current phase.

## Evidence Labels

Classify important information as one of:

- VERIFIED FROM CODE
- VERIFIED FROM CONFIG
- VERIFIED FROM TEST
- VERIFIED FROM GIT
- VERIFIED FROM OFFICIAL SOURCE
- USER-PROVIDED
- NOT VERIFIED
- CONFLICTING EVIDENCE

Do not convert documentation, an AI report, or a prediction into observed evidence.

## Required Work Cycle

UNDERSTAND -> VERIFY -> CHANGE -> TEST -> DOCUMENT -> REVERIFY

For each meaningful change, record what changed, why, files, exact verification, current status, risks, and related notes.

## Prohibited Actions

- No work from a locked later phase.
- No payment execution or real bank-detail change.
- No definitive fraud declaration.
- No private financial data.
- No credentials in files, logs, evidence, or chat.
- No weakening tests or changing benchmark truth to improve results.
- No fabricated commands, outputs, timings, costs, or scores.
- No global Docker prune or unrelated filesystem access.
- No unsupported competitor claims.

## Human-Only Triggers

Ask the human only for a genuine secret, account login, paid-service approval, machine permission, system dependency, or consequential decision. Never request a secret in plain chat when a local environment variable or approved secret store can be used.

## Gate Rule

Local ChatGPT can stop work or mark a packet ready; only External ChatGPT can approve a phase. The next phase unlocks only after the exact verdict `PHASE APPROVED — 100%`.
