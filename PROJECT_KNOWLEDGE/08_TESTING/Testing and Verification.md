# Testing and Verification

## Latest Independent Local Audit

Date: 2026-08-29

Accepted baseline source: `7512b9eace0e43045a406bc7cf46d76e1eb21ea7`

Exact remote clean-clone candidate: `1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c`

| Check | Observed Result |
| --- | --- |
| Accepted provider run | 6/6 SUCCESS using requested/returned `gemini-3.6-flash` |
| Offline evaluator | VALID; 100% recommendations/findings/schema; unsafe PAY 0/5 |
| Existing-report verification | Exit 0; deterministic regenerated report matched |
| Focused Phase 2 suite | Exit 0; 35 passed |
| `verify.ps1` | Exit 0; 81 passed; runtime isolation checks passed |
| Git Bash `./verify.sh` | Exit 0; 81 passed; runtime isolation checks passed |
| Exact remote clean clone | PASS; report verification and both full pipelines passed |
| Missing-key negative path | Exact expected error; exit 1 |
| Post-test clone state | Clean; exact Compose and TEMP resources removed |
| Secret-pattern scan | No common provider-token or private-key patterns |

## Evidence integrity

- Manifest v2 binds normalized public-input hashes, raw output hashes, source artifacts, settings, retry policy, model, SDK, usage metadata, and source commit.
- Per-case wrapper binds the full rendered prompt and its SHA-256.
- Raw successful responses parse exactly to the scored output objects.
- The independent audit recomputed all metrics and checked citations/calculations against public inputs.
- The v1 CRLF portability failure remains preserved and excluded from accepted metrics.

## Current evidence files

- `evidence/phase_2/runs/run_20260829_154058_02e9416b/`
- `evidence/phase_2/final_clean_clone_execution.txt`
- `reports/phase_2_review_packet.md`
- `evidence/phase_1/SHA256_MANIFEST.txt`

Historical `superseded_` logs and INVALID runs are retained but are not current decision evidence.

## Unverified

- Native macOS/Linux execution.
- Vulnerability/CVE scanner results.
- Provider cost; recorded as UNKNOWN.
