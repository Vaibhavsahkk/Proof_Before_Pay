# Known Issues

## Active Gate State

Phase 1 is externally approved. Phase 2 is ACTIVE in remediation following an external `PHASE FAIL` verdict. Phase 3+ remains locked.

## Environment-Specific Shell Invocation

### Observed Behavior
On 2026-08-29, running `bash ./verify.sh` from PowerShell resolved to Windows WSL bash and exited 1 during Compose configuration. Running the same script with `C:\Program Files\Git\bin\bash.exe` exited 0 and completed all current tests and security checks.

### Impact
The reproduction guide must distinguish Git Bash from WSL when launched from PowerShell.

### Status
Known documentation/usability issue; not a failure of the verified Git Bash pipeline.

## Unverified Areas

- Native macOS/Linux execution is unverified.
- No vulnerability/CVE scanner has been run; no remediation claim is made.

## Phase 2 Provider Availability

The first real baseline attempt used 2.5 Pro, but the provider returned HTTP 404 for all six cases. The second used 3.1 Pro but returned HTTP 429 because the account's Pro free-tier quota is zero. Both runs are preserved as INVALID and must not be reported as performance. Decision 008 pins the retry to successfully probed `gemini-3.6-flash`.

## Resolved Input-Hash Portability Defect

A v1 run hashed raw Windows CRLF input bytes and failed verification in a fresh LF checkout. The failure is preserved in `evidence/phase_2/superseded_clean_clone_failure_c21cb36.txt`. Manifest v2 now uses canonical UTF-8 text hashing; the replacement run passed exact remote clean-clone verification.
