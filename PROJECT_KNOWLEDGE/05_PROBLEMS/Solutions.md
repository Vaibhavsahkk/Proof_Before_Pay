# Solutions

## Ground Truth Must Be Available Only to the Verifier

### Problem
The runtime must not contain hidden ground truth, evaluator code, or test artifacts, while the verifier still needs all of them for strict validation.

### Solution
Use separate Docker targets. The `runtime` target copies only application code, the rulebook, public schemas, public cases, and its security scanner. The `verifier` target copies tests, scripts, schemas, evidence manifest, and both public and ground-truth cases.

### Verification
- `tests/test_phase1_validation.py` checks the allowlisted Docker design.
- `verify.ps1` and Git Bash `verify.sh` inspect required runtime inputs.
- Both pipelines inject a forbidden ground-truth mount and require scanner exit exactly 1.
- Both pipelines then scan the normal runtime and require exit 0.

### Files
- `Dockerfile`
- `docker-compose.yml`
- `scripts/verify_container_security.sh`
- `verify.ps1`
- `verify.sh`

## Use the Verified Bash Environment on Windows

From PowerShell, call `C:\Program Files\Git\bin\bash.exe ./verify.sh` when Git Bash is the intended environment. Do not assume the bare `bash` command resolves to Git Bash.
