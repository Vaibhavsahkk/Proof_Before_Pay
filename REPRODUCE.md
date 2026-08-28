# Reproduction Guide

## Phase 0: Environment & Governance

### Prerequisites

- Docker Desktop or Docker Engine with Docker Compose v2
- Git
- PowerShell on Windows, or Bash on POSIX

No model API or `GEMINI_API_KEY` is required for Phase 0.

### 1. Clone the repository

**UNVERIFIED:** no remote URL is configured. `git remote -v` returns no entries.

When the human provides the intended URL:

```bash
git clone <PENDING_URL> micro1-challenge
cd micro1-challenge
```

### 2. Run the adversarial Phase 0 checks

```powershell
.\scripts\run_adversarial_tests.ps1
```

Expected successful result: `HARNESS EXIT: 0` in `evidence/phase_0/adversarial_execution.txt`.

The harness must also show `TEST L WRAPPER: PASS`; this is the recorded full Git Bash/POSIX pipeline check.

### 3. Run the Windows verification pipeline

```powershell
.\verify.ps1
$LASTEXITCODE
```

Expected result: process exit 0. Complete evidence in `evidence/phase_0/pipeline_execution.txt`.

### 4. Run the POSIX verification pipeline

```bash
./verify.sh
```

Expected result: process exit 0.

### 5. Success criteria

A successful run must end with:

```text
[PASS] Recursive Container Security Assertion completed successfully.
************************************************************
ALL VERIFICATION STEPS PASSED
************************************************************
```

The current test tree contains 16 tests.
