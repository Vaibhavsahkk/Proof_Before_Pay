# Trajectories

`raw/` is local/ignored. `sanitized/` contains reviewed representative
trajectories safe for submission.

Never copy secrets into trajectory examples.

## Package contents (2026-09-01 — all REAL execution traces)

Selected from live runs recorded 2026-09-01 (see `trajectory_manifest.json`
for per-file event counts and the secret-scan verification):

| File | Scenario | Source |
|---|---|---|
| `01_clean_pay.json` | Clean PAY, full pipeline, no anomalies (case_001) | UI execution trace |
| `02_hold_duplicate_billing.json` | HOLD + Duplicate Billing + human escalation (case_002) | UI execution trace |
| `03_missing_evidence_investigate.json` | INVESTIGATE + Missing Vendor Master, fail-closed (case_011) | UI execution trace |
| `04_unverified_bank_change.json` | INVESTIGATE + Unverified Bank Change + human escalation (case_005) | UI execution trace |
| `05_credential_failover_recovery.json` | Gemini 429 rate-limit → RetrySignal → key cooldown rotation → retry loop | live quota-constrained run |
| `06_track_b_challenging_case_111.json` | Track B challenging case: duplicate billing + unverified bank change across 6 documents/3 formats → exact ground-truth HOLD (baseline got this wrong) | frozen A4 agent run |

The challenging Track-B case trajectory was added from the completed A4
agent run (`data/track_b/evaluation/agent_runs/frozen_v1_assembly/`), as
promised — a REAL trace, never fabricated.
