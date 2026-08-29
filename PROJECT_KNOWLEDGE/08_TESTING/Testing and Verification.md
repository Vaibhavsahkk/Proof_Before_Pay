# Testing and Verification

## Latest Independent Local Audit

Date: 2026-08-29

Repository HEAD: `adf9a1c1032df5679717acf8691691decc638f49`

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

## Current Evidence Files

- `evidence/phase_1/final_clean_clone_execution.txt`
- `evidence/phase_1/SHA256_MANIFEST.txt`
- `reports/phase_1_review_packet.md`

Historical `superseded_` logs are retained but are not current decision evidence.

## Unverified

- Native macOS/Linux execution.
- Vulnerability/CVE scanner results.
