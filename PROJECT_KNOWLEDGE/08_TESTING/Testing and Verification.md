# Testing and Verification

## Latest Independent Local Audit

Date: 2026-08-29

Corrected Phase 2 scaffold code candidate: `95cebd1`

Phase 2 exact remote clean-clone candidate: `eac35cdb4994f917d76cde4a6ca1749957d65f3f`

Phase 1 tested candidate: `43ba9356aaa110113e81a446cb701bee40f0fc39`

| Check | Observed Result |
| --- | --- |
| `python scripts/validate_phase1.py` | Exit 0; 6/6 cases matched |
| `python scripts/verify_manifest.py` | Exit 0 |
| Focused Phase 1 pytest suite | Exit 0; 29 passed |
| `verify.ps1` | Exit 0; 46 passed; runtime isolation checks passed |
| `C:\Program Files\Git\bin\bash.exe ./verify.sh` | Exit 0; 46 passed; runtime isolation checks passed |
| Bare `bash ./verify.sh` from PowerShell | Exit 1 under WSL; not accepted as passing evidence |
| Vault secret-pattern scan | Exit 0; no matching secret material |

## Phase 2 Scaffold Audit

- Actual Gemini execution: NOT RUN.
- Model performance metrics: UNVERIFIED.
- Corrected focused API-independent suite: 29 passed with deprecation warnings treated as errors.
- Corrected PowerShell and Git Bash Docker pipelines: each passed on committed source `95cebd1` with 75 tests, manifest validation, credential isolation, runtime import, and ground-truth rejection.
- Exact remote clean clone: PASS on `eac35cdb4994f917d76cde4a6ca1749957d65f3f`; 29 focused tests, both 75-test Docker pipelines, exact missing-key rejection, clean Git state, and scoped cleanup passed.
- Phase 3+ remains locked.

## Current Evidence Files

- `evidence/phase_1/final_clean_clone_execution.txt`
- `evidence/phase_1/SHA256_MANIFEST.txt`
- `reports/phase_1_review_packet.md`
- `evidence/phase_2/scaffold_verify_powershell.txt`
- `evidence/phase_2/scaffold_verify_git_bash.txt`
- `evidence/phase_2/scaffold_clean_clone_execution.txt` (normalized machine-captured log)

Historical `superseded_` logs are retained but are not current decision evidence.

## Unverified

- Native macOS/Linux execution.
- Vulnerability/CVE scanner results.
