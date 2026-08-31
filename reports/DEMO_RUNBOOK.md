# Demo Runbook - Proof Before Pay (Reviewer App)

**Purpose:** Step-by-step instructions to launch, verify, demo, and shut down the Track A Reviewer App on a fresh clone. No benchmark/evaluator files are touched by these steps.

## 1. Prerequisites

- Python 3.11+ (project lockfile targets 3.11), Git, PowerShell (Windows) or bash
- `.env` present with at least one live `GEMINI_API_KEY` (for uploads/live extraction; sample cases run from cache without it)
- Install once: `pip install -r requirements.txt`

## 2. Launch the server

```powershell
# Windows (PowerShell) - from repo root d:\MICRO.1
python -m src.ui.server
# Console prints: "Proof Before Pay Reviewer App running at http://127.0.0.1:8080/"
```

```bash
# Linux/macOS
python -m src.ui.server            # default port 8080
python -m src.ui.server 3000        # optional custom port
```

The server binds **127.0.0.1 only** (not exposed to network). Leave this terminal open; it is the demo process.

## 3. Verify (30-second smoke test)

```powershell
Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing      # 200 {"status":"ok",...}
Invoke-WebRequest http://127.0.0.1:8080/api/cases -UseBasicParsing   # lists 12 cases
```

Then open **http://127.0.0.1:8080/** in a browser: the "Proof Before Pay / Review Supplier Payment" page loads with sample case buttons.

Full audit (48 checks, cached mode, no API cost):
```powershell
python -m scripts.qa_demo_environment
# Writes reports/DEMO_ENVIRONMENT_QA_RESULTS.json - expect 100% pass
# Optional live upload probes: python -m scripts.qa_demo_environment --live
```

## 4. Demo script (5 minutes)

1. **Opening:** "Small businesses lose money to invoice errors. Proof Before Pay reviews every supplier payment before you pay it - with a full audit trail."
2. **Sample case (instant path):** click `case_001` (clean payment) -> Start -> shows **PAY** with reasoning and confidence in seconds (served from evaluation cache).
3. **Discrepancy detection:** click `case_005` (amount mismatch) -> **HOLD/INVESTIGATE** with findings that show the exact rule violations (vendor/amount/P.O. checks).
4. **Smart Review (live AI path):** upload the sample bundle from `scratch_test_docs/` (purchase_order.json + vendor_master.json + invoice_bad_amount.json) -> agent extracts fields live (7-15s), then rules engine decides.
5. **Audit trail (the differentiator):** open the Trace tab -> full event-by-event timeline (tool calls, inputs, outputs, memory) - "every decision is reproducible and explainable."
6. **Close:** "12/12 benchmark cases match ground truth; deterministic rule engine on top of AI extraction; no payment leaves without proof."

## 5. Recovery / troubleshooting

| Symptom | Fix |
|---|---|
| Port already in use | `python -m src.ui.server 3001` (any free port) or kill stale python: `Get-Process python \| Stop-Process` |
| Blank page at :8080 | Confirm exact URL `http://127.0.0.1:8080/`; check console for startup errors |
| Upload times out / 500 | `.env` missing or key exhausted -> server falls back to cached path; check `server_log` output; credential failover rotates to next key automatically |
| Recommendations look wrong | Re-run `python -m scripts.qa_demo_environment` and diff against `reports/DEMO_ENVIRONMENT_QA_RESULTS.json` baseline |
| Trace tab empty | Normal if no investigation ran yet this session; run any case first; or open `traces/raw/<latest>.jsonl` directly |
| VM reboot mid-demo | Cached cases unaffected (no state needed); re-launch server per step 2 and continue |

## 6. Shutdown

Close the server terminal (Ctrl+C), or:
```powershell
Get-Process python | Where-Object {$_.Path -like "*python*"} | Stop-Process
```
No cleanup needed: traces and agent memory are append-only runtime artifacts and do not affect benchmark/evaluator files.

## 7. Boundaries (what demo steps never touch)

- No writes to `benchmark/`, `eval/`, `baseline/`, `data/cases/ground_truth/`, or any `scripts/evaluate*` file
- Secrets stay in `.env`; the UI/API never returns key material
- Known non-blocking observations (trace path containment, trace file accumulation) are tracked in `reports/DEMO_ENVIRONMENT_QA.md` Issue Classification (P2/P3)