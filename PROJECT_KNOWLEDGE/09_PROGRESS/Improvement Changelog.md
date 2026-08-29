# Improvement Changelog

This note records only experiments that were actually run. Do not pre-fill predicted scores or invented outcomes.

| Stage | What Was Tried and Why | Evidence | Result | Decision / Learning |
| --- | --- | --- | --- | --- |
| Phase 1 benchmark foundation | Defined strict schemas, rulebook, deterministic oracle, manifest, and runtime/verifier isolation | `reports/phase_1_review_packet.md` and `evidence/phase_1/final_clean_clone_execution.txt` | Phase 1 externally approved; no baseline score exists yet | Keep as the frozen evaluation foundation |
| Baseline attempt 1 | Pinned `gemini-2.5-pro` with the frozen prompt and six public cases | `evidence/phase_2/runs/run_20260829_151625_260ba740` | INVALID: all six provider calls returned HTTP 404; no valid performance metric | Preserve the failed attempt and pin the provider-supported concrete `gemini-3.1-pro-preview` model before retrying |
| Valid baseline | NOT RUN - Phase 2 active | None | NOT VERIFIED | Run only from a clean committed source using the frozen benchmark |
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
