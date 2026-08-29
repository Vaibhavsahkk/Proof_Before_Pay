# Known Issues

## Active Gate State

Phase 1 is externally approved. Phase 2 Fair Baseline is active. Phase 3+ remains locked.

## Environment-Specific Shell Invocation

### Observed Behavior
On 2026-08-29, running `bash ./verify.sh` from PowerShell resolved to Windows WSL bash and exited 1 during Compose configuration. Running the same script with `C:\Program Files\Git\bin\bash.exe` exited 0 and completed all 46 tests and security checks.

### Impact
The reproduction guide must distinguish Git Bash from WSL when launched from PowerShell.

### Status
Known documentation/usability issue; not a failure of the verified Git Bash pipeline.

## Unverified Areas

- Native macOS/Linux execution is unverified.
- No vulnerability/CVE scanner has been run; no remediation claim is made.
- The actual Gemini baseline has not run, so Phase 2 metrics remain unverified.

## Phase 2 Provider Availability

The first real baseline attempt used 2.5 Pro, but the provider returned HTTP 404 for all six cases. The second used 3.1 Pro but returned HTTP 429 because the account's Pro free-tier quota is zero. Both runs are preserved as INVALID and must not be reported as performance. Decision 008 pins the retry to successfully probed `gemini-3.6-flash`.
