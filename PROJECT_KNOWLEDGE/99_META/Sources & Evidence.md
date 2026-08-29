# Sources & Evidence

This vault's knowledge is derived strictly from the following verifiable sources within `D:\MICRO.1`:

## Core Project Source of Truth
- `docs/SOURCE_OF_TRUTH.md`: Defines the authority order.
- `sources/official_micro1_hackathon.pdf`: Official hackathon rules and deliverables.
- `sources/Idea to work.txt`: Original candidate pool.
- `docs/LOCKED_PROBLEM.md`: Locked project decision and hard boundaries.
- `STATUS.md` plus executable artifacts: Current engineering state.
- `PLAN.md`: Phase gates and exit criteria.

## Documentation
- `docs/PHASE_1_SCOPE.md` (VERIFIED)
- `benchmark/RULEBOOK.md` (VERIFIED)
- `eval/EVAL_DESIGN.md` (VERIFIED)

## Pipeline Logs & Artifacts
- `evidence/phase_1/final_clean_clone_execution.txt` (VERIFIED)
- `evidence/phase_1/SHA256_MANIFEST.txt` (VERIFIED)
- `evidence/phase_2/runs/run_20260829_154058_02e9416b/` (VERIFIED)
- `evidence/phase_2/final_clean_clone_execution.txt` (VERIFIED)
- `reports/phase_2_review_packet.md` (CURRENT REVIEW PACKET)

## Git History
- Recent commits by `Execution Engineer` confirming Phase 1 fixes and pipeline updates on 2026-08-29 (VERIFIED).

## Local Knowledge Audit Evidence
- Obsidian executable: version 1.13.7 at the installed local-programs path.
- Vault opened successfully as `PROJECT_KNOWLEDGE` on 2026-08-29.
- Focused Phase 1 tests: 29 passed.
- `verify.ps1`: exit 0, 46 passed.
- Git Bash `verify.sh`: exit 0, 46 passed.
- Vault credential-pattern scan: PASS; no matching secret material found.
- Bare WSL `bash ./verify.sh`: exit 1 and is not accepted as passing evidence.
- Phase 2 focused tests: 35 passed.
- Current PowerShell and Git Bash Docker pipelines: 81 passed each.
- Phase 2 committed report re-verification: exit 0.
- Phase 2 exact remote clean-clone gate: PASS.

## Note on Unverified Claims
Any unverified claims, assumed future architecture, or unverified environment constraints (like native macOS/Linux POSIX tests) are explicitly marked as NOT VERIFIED or UNKNOWN.
