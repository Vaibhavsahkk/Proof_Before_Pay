# Representative Trajectories Plan

**Prepared by:** Parallel Evidence / Submission Preparation Agent
**Date:** 2026-08-31
**Status:** PLAN ONLY. No trajectory files were fabricated, and no raw traces were modified. Raw traces in `traces/raw/` were only read, never written. `traces/raw/` is gitignored by policy, so the sanitized derivatives described here must be created (by a later authorized step) into `traces/sanitized/` and/or `trajectories/sanitized/`.

## 1. Existing trace/trajectory infrastructure (inspected)

| Artifact | Location | Status |
| --- | --- | --- |
| JSONL trace writer | `src/utils/logger.py` (`TraceLogger`) | Tracks: `timestamp`, `run_id`, `phase` (extract/verify/apply_rules/explain/validate/escalate), `agent`, `action`, `tool`, `input`, `output`, `result` (STARTED/SUCCESS/ERROR), `error`, `latency_ms`, `metadata`. Applies recursive sanitization + secret-pattern redaction at write time. |
| Raw trace store | `traces/raw/trace_*.jsonl` | Local only; gitignored (`traces/raw/`, `traces/*.jsonl`). 40+ files on disk; NOT suitable for direct submission. |
| Sanitized trace store | `traces/sanitized/` | The one previously committed file (`trace_20260828_131408_7428b4c6.jsonl`) is now DELETED in the working tree; directory is currently empty on disk. |
| Trajectories dir | `trajectories/raw/` (gitignored), `trajectories/sanitized/example_trace.json` | `example_trace.json` is a 2-event dummy placeholder with `[REDACTED_INVOICE_DATA]` — not a real trajectory. |
| Policy guard | `verify.ps1` / `verify.sh` | Fail the pipeline if any trace outside `traces/sanitized/` and any trajectory outside `trajectories/sanitized/` is git-tracked. This protects against accidental secret-bearing trace commits. |
| UI trace viewer | `src/ui/server.py` `GET /api/trace` | Serves latest (or requested) raw trace events to the UI "Audit & Connection Log" tab. |

**Conclusion:** the infrastructure fully supports producing judge-ready trajectories; what is missing is a curated, sanitized, committed set. This plan defines that set without creating it.

## 2. Recommended committed set (6-8 files, small and complete)

Selection principle: one trajectory per distinct judge-relevant capability; each must come from a REAL run; each must be reviewed and redacted before commit.

### T1 — Clean PAY
- **Scenario:** `case_001` (or `case_012`, the verified-bank-change PAY exception) — all documents present, all deterministic checks pass, LLM extraction succeeds, output `PAY` with four/five evidence references and the four calculator calls.
- **Required evidence:** CLI run or UI run of `python -m src.main --file data/cases/public/case_001.json`; trace with `phase` events extract -> verify -> apply_rules -> explain -> validate; final output contract object.
- **Required trace fields:** `run_id`, per-stage `phase`/`action`/`tool`/`result`, `deterministic_calculation_references` (proving calculator.multiply / sum_values / calculate_tax / check_equality actually ran), `evidence_references`, `latency_ms`.
- **Sensitive data to remove:** any API-key residue (masked form e.g. `AQ.A...rXsA` is acceptable as it demonstrates masking; confirm no full key), full prompt text if it embeds internal instructions (keep as citation), any path leaking local usernames (scrub `C:\Users\...`).
- **Judge takeaway:** a "safe" recommendation is not vibes — it is four verified documents plus deterministic arithmetic, logged stage by stage.

### T2 — Multi-finding HOLD
- **Scenario:** `case_006` (Duplicate Billing + Unverified Bank Change) or `case_008` (Currency Mismatch + Invalid Currency) — proves the agent does not short-circuit on the first anomaly.
- **Required evidence:** trace showing verify phase emitting MULTIPLE anomalies, apply_rules receiving the full list, and the final findings array containing both entries; rule precedence HOLD.
- **Required trace fields:** anomaly list in the verify `output`, `findings` array, escalation event (`phase: escalate`, result ESCALATED).
- **Sensitive data to remove:** as T1.
- **Judge takeaway:** finding completeness — overlapping issues are all surfaced, and the human reviewer sees every one.

### T3 — Missing-evidence INVESTIGATE
- **Scenario:** `case_011` (Missing Vendor Master) — vendor master absent; dependent checks skipped and reported as skipped, missing evidence flagged, fail-safe INVESTIGATE.
- **Required evidence:** trace where verify records `checks_skipped` (vendor identity check), finding "Missing Vendor Master", `missing_evidence` populated, escalation to human.
- **Required trace fields:** `checks_performed` vs `checks_skipped` separation (available via orchestrator state; exposed through the API contract `checks_performed`/`checks_skipped`), `missing_evidence` array, `required_human_next_step`.
- **Sensitive data to remove:** as T1.
- **Judge takeaway:** absence of evidence changes the behavior deterministically — the system neither guesses nor silently skips.


### T4 — Credential failover / state-preserving recovery
- **Scenario:** a real `429 RESOURCE_EXHAUSTED` during `extract` (naturally observed; see `reports/phase_4_9A_live_recovery_closure.md`) with key rotation and same-stage resume.
- **Required evidence:** trace events: `extract` STARTED, ERROR with `429 RESOURCE_EXHAUSTED`, `retry_wait` WARNING, credential slot rotation (masked), `extract` resumed on next slot, SUCCESS, final valid output.
- **Required trace fields:** `error` containing the 429 text, `retry_wait` event, masked slot identifiers (e.g. `AQ.A...rXsA` -> `AQ.A...6Ikw`), same `run_id` throughout (proving no restart), final output contract.
- **Sensitive data to remove:** full API keys (masked form is fine and desirable — it demonstrates masking); the raw provider error JSON may embed project IDs — verify and scrub.
- **Judge takeaway:** quota failure is handled by design (rotation + same-point resume), not by crashing or by guessing.

### T5 — Pool exhaustion / fail-closed
- **Scenario:** all credentials exhausted (controlled: `tests/test_credential_failover.py` simulates `case_429` exhaustion; live: `reports/phase_4_8_runtime_and_reproducibility_remediation.md` V-15 observed real exhaustion).
- **Required evidence:** trace with `workflow` ERROR "All credentials exhausted", and the fail-closed output: `recommendation: INVESTIGATE`, findings `["All credentials exhausted"]`, human next step.
- **Required trace fields:** the exhaustion ERROR event, the fail-closed output object, absence of any PAY.
- **Sensitive data to remove:** as T4.
- **Judge takeaway:** the most severe failure mode still cannot produce an unsafe PAY — the safety floor is structural.

### T6 — Smart Review on a new document (unstructured input)
- **Scenario:** PDF/image intake through `DocumentAdapter` (`verify_smart_review_gatekeeper.py` Check 1&2: price contradiction in a synthetic PDF; or Check 3&4 multi-document bundle) — automatic anomaly discovery with NO user-selected anomaly hint.
- **Required evidence:** trace of a `case_999`/`case_000`-style run over a PDF bundle: DocumentAdapter ingestion, LLM extraction from raw text, deterministic checks, findings discovered automatically.
- **Required trace fields:** ingestion/adapter event or metadata, extraction output, discovered findings, final recommendation (HOLD/INVESTIGATE for the contradiction PDF).
- **Sensitive data to remove:** as T1; confirm the synthetic PDF content is the repo's own synthetic text (it is, per `verify_smart_review_gatekeeper.py`).
- **Judge takeaway:** the agent generalizes beyond pre-modeled JSON cases to real document formats, without hints.

### T7 — Track-B result trajectory — **PENDING REAL MEASUREMENT**
- **Scenario:** a representative messy real-world Track-B case once Track-B exists (Phase A1, other agent) and is run (A4).
- **Status:** DO NOT create this trajectory now. Track-B cases/runs do not exist yet. Creating it now would be fabricating a result.
- **Judge takeaway (future):** how the same architecture behaves when documents are noisy, incomplete, or adversarial.

### T8 — Verification-loop trajectory — **PENDING, ONLY IF IMPLEMENTED**
- **Scenario:** an agent self-check/retry loop around deterministic verification, if such a feature is ever implemented and measured.
- **Status:** NOT IMPLEMENTED. If it never ships, delete this entry. Never stage a simulated loop as real evidence.

## 3. Sanitization and packaging rules (for the later authorized commit step)

1. Source only from REAL runs (live or controlled tests); never hand-edit event content — only redact.
2. Run the existing sanitizer semantics (`TraceLogger.sanitize_value` patterns) as a first pass; then manually review every field.
3. Scrub: full API keys (keep masked forms), absolute local paths with usernames, provider project/account IDs inside error JSON, any `.env`-derived value.
4. Keep `run_id` continuity within a file (it proves single-run integrity) but randomize or drop cross-file correlation that isn't needed.
5. Commit ONLY under `traces/sanitized/` and/or `trajectories/sanitized/` (pipeline-enforced allowlists). Raw traces stay untracked.
6. Pair each committed trajectory with a 3-5 line README entry: scenario, source command, date, redaction notes, and the expected judge takeaway from §2.
7. Record the source trace's SHA-256 in the README so a judge can verify no content was invented post-hoc beyond redaction.

## 4. What a judge should be able to reconstruct from the set

From T1-T6 alone: (a) the LLM's actual role (extraction + explanation only); (b) that every number passes through deterministic tools; (c) precedence and multi-finding behavior; (d) absence-of-evidence handling; (e) resilience (failover, fail-closed); (f) generalization to unstructured documents. T7-T8 extend the story only if/when they are real.
