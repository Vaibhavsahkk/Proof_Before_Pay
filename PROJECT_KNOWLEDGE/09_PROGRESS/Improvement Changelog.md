# Improvement Changelog

This note records only experiments that were actually run. Do not pre-fill predicted scores or invented outcomes.

| Stage | What Was Tried and Why | Evidence | Result | Decision / Learning |
| --- | --- | --- | --- | --- |
| Phase 1 benchmark foundation | Defined strict schemas, rulebook, deterministic oracle, manifest, and runtime/verifier isolation | `reports/phase_1_review_packet.md` and `evidence/phase_1/final_clean_clone_execution.txt` | Phase 1 externally approved; no baseline score exists yet | Keep as the frozen evaluation foundation |
| Baseline attempt 1 | Pinned `gemini-2.5-pro` with the frozen prompt and six public cases | `evidence/phase_2/runs/run_20260829_151625_260ba740` | INVALID: all six provider calls returned HTTP 404; no valid performance metric | Preserve the failed attempt; provider retired this model for new users |
| Baseline attempt 2 | Pinned `gemini-3.1-pro-preview` after the provider recommendation | `evidence/phase_2/runs/run_20260829_152146_25ba3699` | INVALID: all six calls returned HTTP 429 because Pro free-tier quota is zero | Avoid requiring paid billing; use successfully probed concrete `gemini-3.6-flash` |
| Baseline attempt 3 | Ran `gemini-3.6-flash` from clean source with manifest v1 | `evidence/phase_2/runs/run_20260829_152514_caab4d45` and `evidence/phase_2/superseded_clean_clone_failure_c21cb36.txt` | Superseded: local evaluation VALID, but fresh-clone input hashes failed because raw bytes depended on CRLF checkout state | Preserve outputs; exclude metrics; canonicalize text hashes and version the manifest |
| Accepted baseline | Re-ran pinned `gemini-3.6-flash` with manifest v2 canonical input hashing | `evidence/phase_2/runs/run_20260829_154058_02e9416b` and `evidence/phase_2/final_clean_clone_execution.txt` | VALID: 100% recommendation/findings/schema, unsafe PAY 0/5; exact clean-clone PASS | Submit Phase 2 for external review; make no production-generalization claim |
| Agent iterations | NOT RUN - later phases locked | None | NOT VERIFIED | Add entries only after real experiments |

## Entry Template

### Change

#### What Changed

#### Why

#### Files

#### Exact Verification

#### Observed Result

#### Decision / Learning

#### Related
