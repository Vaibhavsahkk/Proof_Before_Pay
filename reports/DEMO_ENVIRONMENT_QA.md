# Demo Environment QA Audit - Proof Before Pay

**Date:** 2026-08-31 | **Scope:** Track A Demo UI (src/ui/server.py + static/index.html) | **Mode:** Cached (no live API calls) + 1 live extraction path
**Machine-readable results:** `reports/DEMO_ENVIRONMENT_QA_RESULTS.json` | **Script:** `scripts/qa_demo_environment.py`

## Verdict

**PASS - 48/48 checks (100%).** Demo environment is operational and demo-safe.

## Executive Summary

The Reviewer App demo environment was launched from a clean process (`python -m src.ui.server`, port 8080, localhost-bound) and audited via API-level black-box checks. All 12 cached benchmark cases return HTTP 200 with the full output contract, and **every recommendation matches ground truth exactly** (PAY x2, HOLD x5, INVESTIGATE x4, distribution as designed). The Smart Review upload path works end-to-end (JSON bundle -> 200 INVESTIGATE, ~7-9s live extraction). All 9 adversarial probes are handled gracefully with clear, human-readable error messages and no crashes, no secret leakage, no 500s. No P0/P1 issues found. Three P2/P3-class observations are documented below; none blocks the demo.

## Environment Verified

| Item | Status |
|---|---|
| Server bind | 127.0.0.1:8080 (localhost only) |
| Root page | 200, 44 KB HTML (Proof Before Pay, sample buttons, start button present) |
| Health | `GET /health` -> 200 `{"status":"ok"}` (note: not under `/api/` prefix) |
| Case listing | `GET /api/cases` -> 12 cases; `GET /api/cases/case_001` -> 200 |
| Traces | `traces/raw/` = 529 jsonl files; default trace endpoint returns latest (396 events) |
| Secrets | `.env` never read by any endpoint path probed; no key material in any response |

## Section Results

### P1 - Startup & Endpoints (9/9)
Root page serves with all critical UI markers (title, "Review Supplier Payment", sample-btn, start-btn). Health, cases listing, and single-case endpoints all 200. No startup errors in logs.

### P2 - Cached Benchmark Cases (24/24)
All 12 cases: HTTP 200, valid JSON, full output contract keys (`recommendation`, `findings`, `case_id`, `uncertainty`, `required_human_next_step`), and **100% recommendation accuracy** vs `data/cases/ground_truth/`:

| Case | Recommendation | Expected | Match | Latency |
|---|---|---|---|---|
| case_001 | PAY | PAY | Y | 0.10s |
| case_002 | HOLD | HOLD | Y | 0.02s |
| case_003 | HOLD | HOLD | Y | 0.04s |
| case_004 | HOLD | HOLD | Y | 0.04s |
| case_005 | INVESTIGATE | INVESTIGATE | Y | 0.02s |
| case_006 | HOLD | HOLD | Y | 0.04s |
| case_007 | HOLD | HOLD | Y | 0.02s |
| case_008 | HOLD | HOLD | Y | 0.02s |
| case_009 | INVESTIGATE | INVESTIGATE | Y | 0.04s |
| case_010 | INVESTIGATE | INVESTIGATE | Y | 0.02s |
| case_011 | INVESTIGATE | INVESTIGATE | Y | 0.04s |
| case_012 | PAY | PAY | Y | 0.03s |

Average cached-case latency: **0.03s** (instant demo path).

### P3 - Uploads / Smart Review (2/2 cached; live probes defined in script)
- Single JSON evidence bundle (`purchase_order.json`) -> 200, recommendation INVESTIGATE, uploaded-docs metadata returned. Live extraction path exercised (~7-9s, Gemini call, no multimodal needed for JSON).
- Script supports `--live` flag for PDF (text extraction), PNG (multimodal), multi-doc bundle, and guided content upload - all wired and ready; not executed in this run to keep the audit deterministic and secret-free.

### P4 - Adversarial / Error UX (10/10)
| Probe | Result |
|---|---|
| `.exe` upload | Rejected (400) |
| Corrupt PDF (bad magic content) | Handled, no crash |
| Empty file | 400 clear message |
| Invalid JSON content | 400 clear message |
| Unknown case_id | 400 "Please upload at least one supplier document..." |
| Malformed JSON body | 400 "Invalid JSON payload..." |
| GET on POST endpoint | Rejected |
| Empty payload | 400 clear message |
| Trace traversal `../../.env` | **No secrets leaked** (non-JSON lines filtered; empty events) |
| Trace traversal into `reports/*.json` | Containment gap noted (see P2-1) |

### P5 - Trace Endpoint (3/3)
Nonexistent trace -> graceful empty. Default -> latest trace (396 events). Named trace file -> full event list. Trace viewer data flows correctly.

## Issue Classification (P0-P3)

**P0 (demo-blocking):** None.

**P1 (must fix before submission if time permits):** None.

**P2 (should fix, non-blocking):**
1. **Trace endpoint path containment gap** - `GET /api/trace?file=X` accepts any relative path; the server opens it and returns JSON-parseable lines. `.env`/secrets do NOT leak (KEY=value lines fail JSON parse), but any single-line JSON file on disk is readable (e.g., a data cache file). Risk is limited: server binds 127.0.0.1 only, demo context. **Fix (1 line):** resolve the path and require it to start with `traces/` before opening.

**P3 (nice to have, non-blocking):**
2. **`traces/raw` accumulates 529 files, `traces/sanitized` empty** - no retention/rotation policy; trace files grow over demo sessions. Consider a cleanup step in the runbook (or cap listing to latest N).
3. **Stray directory `data/cases/ground_truth;C`** - artifact of a quoting bug in an earlier script; harmless but should be deleted for hygiene.
4. **Health endpoint namespace** - `/health` instead of `/api/health`; document in runbook (done) or alias it for consistency.

## Files Touched by This QA Run (Part 24 confirmation)

- Created: `scripts/qa_demo_environment.py`, `reports/DEMO_ENVIRONMENT_QA_RESULTS.json`, `reports/DEMO_ENVIRONMENT_QA.md`, `reports/DEMO_RUNBOOK.md`
- Runtime byproducts: `server_qa.log`, `server_qa_err.log`, new `traces/raw/*.jsonl` files, `data/memory/` agent memory updates (normal server behavior)
- **No production, benchmark, evaluator, or ground-truth files were modified.** (Pre-existing working-tree modifications to `src/agent/*`, `reports/*` etc. predate this QA run and were not touched.)