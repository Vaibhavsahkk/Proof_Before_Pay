# Testing and Verification

## Latest Independent Local Audit

Date: 2026-08-29

Last committed Phase 2 scaffold before current remediation: `5e9b18f4e4bdbbef8633e4e12f8f1fa8ec441f6d`

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
- Corrected PowerShell and Git Bash Docker pipelines: each passed before commit with 73 tests at that checkpoint; final clean-commit reruns remain required.
- Phase 3+ remains locked.

## Current Evidence Files

- `evidence/phase_1/final_clean_clone_execution.txt`
- `evidence/phase_1/SHA256_MANIFEST.txt`
- `reports/phase_1_review_packet.md`

Historical `superseded_` logs are retained but are not current decision evidence.

## Unverified

- Native macOS/Linux execution.
- Vulnerability/CVE scanner results.
