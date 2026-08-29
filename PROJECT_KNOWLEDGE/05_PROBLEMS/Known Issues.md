# Known Issues

## Active Gate State

Phase 1 is technically ready for external review but is not approved. Phase 2 remains locked.

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
- Remote `git ls-remote` did not return within the local audit timeout. Local `HEAD` and the existing `origin/master` tracking ref both equal `adf9a1c1032df5679717acf8691691decc638f49`.
