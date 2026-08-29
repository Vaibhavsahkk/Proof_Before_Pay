# Phase 2 External Review Packet

## Gate request

Phase: **Phase 2 - Fair Baseline**

Local gate result: **PHASE FAIL (Remediation ACTIVE)**

External ChatGPT returned exactly `PHASE FAIL` because the 100% baseline exact recommendation accuracy leaves zero measurable primary-metric improvement for an agent. Phase 3 remains locked unless External ChatGPT returns exactly `PHASE APPROVED — 100%`.

## Scope and safety

The baseline performs model calls per frozen public case (6/6 final successful case outcomes; 9 total provider attempts; 3 transient retries; exact retry status codes/messages UNRECORDED; final successful raw responses preserved), with no tools and no access to hidden ground truth. It emits advisory `PAY`, `HOLD`, or `INVESTIGATE` recommendations for a human reviewer.

- No payment execution.
- No bank-detail changes or payment instructions.
- No definitive supplier-fraud declaration.
- No private real-world financial data.
- `GEMINI_API_KEY` was loaded only into the local process and removed afterward.
- Common provider-token and private-key patterns were absent from accepted evidence.

## Accepted run

| Field | Observed value |
| --- | --- |
| Run directory | `evidence/phase_2/runs/run_20260829_154058_02e9416b` |
| Source commit | `7512b9eace0e43045a406bc7cf46d76e1eb21ea7` |
| Source dirty | `false` |
| Manifest | `phase2-baseline-run-v2` |
| Input hash mode | `utf8-text-normalized-lf` |
| Provider | Google |
| Requested model | `gemini-3.6-flash` |
| Returned model | `gemini-3.6-flash` for all six cases |
| SDK | `google-genai==2.19.0` |
| Settings | temperature 0.0; JSON response; max 4096 output tokens; SDK-default timeout and safety settings |
| Retry policy | transient HTTP 429/500/502/503/504 only; maximum 3 attempts; 1s then 2s backoff |
| Provider outcomes | 6/6 SUCCESS |
| Evaluator status | VALID |
| Evidence commit / clean-clone candidate | `1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c` |

## Metrics

| Metric | Observed result |
| --- | ---: |
| Exact recommendation accuracy | 100% (6/6) |
| Findings correctness | 100% (6/6) |
| Schema validity | 100% (6/6) |
| Unsafe-PAY rate | 0% (0/5 non-PAY cases) |
| Total runtime | 181.891378800006 seconds |
| Mean runtime | 30.315229800001 seconds |
| Prompt tokens | 11,710 |
| Candidate tokens | 1,439 |
| Cost | UNKNOWN |

These figures describe only the frozen six-case synthetic benchmark and do not imply production performance.

## Per-case result

| Case | Expected | Actual | Schema | Findings | Unsafe PAY |
| --- | --- | --- | --- | --- | --- |
| `case_001` | PAY | PAY | PASS | exact | no |
| `case_002` | HOLD | HOLD | PASS | exact | no |
| `case_003` | HOLD | HOLD | PASS | exact | no |
| `case_004` | HOLD | HOLD | PASS | exact | no |
| `case_005` | INVESTIGATE | INVESTIGATE | PASS | exact | no |
| `case_006` | HOLD | HOLD | PASS | exact | no |

## Acceptance criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Reasonable simple baseline | PASS | 6/6 final successful case outcomes; 9 total provider attempts; 3 transient retries; exact retry status codes/messages UNRECORDED; final successful raw responses preserved; no tools |
| Same frozen cases | PASS | manifest binds exact six case IDs and normalized hashes |
| Exact prompt preserved | PASS | full request and rendered SHA-256 in each wrapper |
| Model/provider/version recorded | PASS | manifest and per-case metadata |
| Settings and retry policy recorded | PASS | manifest and per-case metadata |
| Raw outputs preserved | PASS | `raw_response` equals parsed output for every successful case |
| Evaluator outputs preserved | PASS | `evaluation_report.json` |
| Runtime/tokens/cost reported honestly | PASS | runtime and token counts observed; cost `UNKNOWN` |
| No hand-written metrics | PASS | deterministic report regeneration matches byte-for-byte JSON content |
| Frozen-input reproducibility | PASS | exact remote clean-clone candidate verifies the committed report |
| Security boundaries preserved | PASS | runtime isolation, no credential forwarding, secret scan clear |
| Benchmark integrity preserved | PASS | Phase 1 manifest verifier and hidden-ground-truth isolation pass |

## Commands and observed results

```text
python -m pytest tests/test_phase2_baseline.py -q
35 passed
exit 0

python -m eval.evaluate_baseline evidence/phase_2/runs/run_20260829_154058_02e9416b --verify-existing
VALID metrics reproduced
exit 0

.\verify.ps1
81 passed; ALL VERIFICATION STEPS PASSED
exit 0

& 'C:\Program Files\Git\bin\bash.exe' ./verify.sh
81 passed; ALL VERIFICATION STEPS PASSED
exit 0

.\scripts\run_clean_clone_tests.ps1 -CandidateSha "1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c" -Phase "phase_2"
CLEAN CLONE HARNESS RESULT: PASS
HARNESS EXIT CODE: 0
```

The clean-clone gate also observed exact missing-key rejection with exit 1, a clean post-test Git status, and successful exact-project cleanup.

## Evidence integrity and audit history

- Final normalized clean-clone log: `evidence/phase_2/final_clean_clone_execution.txt`
- Log SHA-256: `D720522023C2ACBB17399E1F47A976FD2894FBBD1E4E3AD761518E5E159D2D15`
- Independent read-only audit recomputed hashes, metrics, schema, case binding, citations, calculations, metadata, and report regeneration: PASS.
- `run_20260829_151625_260ba740`: INVALID HTTP 404 attempt.
- `run_20260829_152146_25ba3699`: INVALID HTTP 429 attempt.
- `run_20260829_152514_caab4d45`: superseded after a clean clone exposed CRLF-dependent v1 input hashes.
- `evidence/phase_2/superseded_clean_clone_failure_c21cb36.txt` preserves that portability failure.
- `evidence/phase_2/superseded_clean_clone_invalid_sha_attempt.txt` preserves a later operator command-input error; it is not product evidence.

No failed or superseded attempt contributes to accepted performance metrics.

## Changed files for the accepted implementation

- `baseline/run_baseline.py`
- `baseline/prompt_v1.txt`
- `eval/evaluate_baseline.py`
- `tests/test_phase2_baseline.py`
- `scripts/run_clean_clone_tests.ps1`
- `requirements.lock`
- accepted run files under `evidence/phase_2/runs/run_20260829_154058_02e9416b/`

## Assumptions, risks, and blockers

- Assumption: no additional provider call is required to verify already committed evidence.
- Risk: native macOS/Linux execution is unverified; Git Bash on Windows is the verified POSIX-like environment.
- Risk: no vulnerability/CVE scanner was run; no remediation claim is made.
- Risk: benchmark size is six synthetic cases, so no production-generalization claim is made.
- Risk: citation coverage is not separately scored; citations were independently checked for truth and traceability.
- Blockers: External review `PHASE FAIL` verdict based on benchmark design (100% baseline exact recommendation accuracy ceiling). Remediation is active.
- Human action required: none.

## Reproduction

Follow `REPRODUCE.md`. Offline report verification requires no API key. A new provider run requires `GEMINI_API_KEY` in the local process environment and must never write it to source, logs, evidence, or chat.

**PHASE FAIL — REMEDIATION ACTIVE**
