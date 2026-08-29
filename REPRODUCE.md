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

**VERIFIED:** repository URL is configured and clean clones successfully into Windows `%TEMP%` without filename limits. The tested candidate commit is `49358817c8481ca0bf3eaa6b5b1d2ddaa015cf96`. Subsequent commits exist only to store executed test evidence without altering executable code.

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

The current test tree contains 25 tests.

## Phase 1: Problem Scope & Benchmark Design

### 1. Data Generation and Manifest
The Phase 1 data is generated using the schema rules:
```bash
python scripts/generate_phase1_data.py
python scripts/generate_manifest.py
```

### 2. Validation Execution
To locally run the deterministic Phase 1 oracle, strict JSON schema validation, and leakage tests:
```bash
python scripts/validate_phase1.py
pytest tests/test_phase1_validation.py
pytest tests/test_manifest.py
```
This is also included by default when executing `./verify.sh` or `.\verify.ps1`.
