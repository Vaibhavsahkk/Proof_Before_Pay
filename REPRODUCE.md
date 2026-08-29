# Reproduction Guide

## Phase 0: Environment & Governance

### Overview

- **Repository:** `https://github.com/Vaibhavsahkk/Proof_Before_Pay.git`
- **Approximate runtime:** 1-2 minutes
- **API/Service cost:** $0 for Phase 0

### Prerequisites

- **Docker Desktop** or Docker Engine with Docker Compose v2
- **Git**
- **PowerShell** on Windows, or **Git Bash/Bash** on POSIX

No model API or `GEMINI_API_KEY` is required for Phase 0.

### Tested toolchain

Observed on the Windows verification host on 2026-08-29:

- Git `2.54.0.windows.1`
- Docker CLI `29.6.2` (build `dfc4efb`)
- Docker Compose `v5.3.1`
- PowerShell `7.6.4`
- Git Bash `5.3.9(1)-release`
- Container Python `3.12.x`, pinned through the Docker base-image digest

These are the recorded tested versions, not minimum-version claims.

### 1. Clone the repository

**VERIFIED:** repository URL is configured and clean clones successfully into Windows `%TEMP%` without filename limits. The tested candidate commit is `ddca58b880b973c7f91df5d89e95402d7bbe54cf`. Subsequent commits exist only to store executed test evidence without altering executable code.

```bash
git clone https://github.com/Vaibhavsahkk/Proof_Before_Pay.git micro1-challenge
cd micro1-challenge
```

### 2. Run the adversarial Phase 0 checks

```powershell
.\scripts\run_adversarial_tests.ps1
```

Expected successful result: `HARNESS EXIT: 0` in `evidence/phase_0/adversarial_execution.txt`.

### 3. Run the Windows verification pipeline

```powershell
.\verify.ps1
$LASTEXITCODE
```

Expected result: process exit 0. Complete evidence in `evidence/phase_0/pipeline_execution.txt`.

### 4. Run the Bash verification pipeline

```bash
./verify.sh
```

Expected result: process exit 0.

The recorded Phase 0 run used Git Bash on Windows. Native macOS/Linux execution remains unverified.

### 5. Success criteria

A successful run must end with:

```text
[PASS] Recursive Container Security Assertion completed successfully.
************************************************************
ALL VERIFICATION STEPS PASSED
************************************************************
```

The current test tree contains 17 tests.
