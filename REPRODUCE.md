# Reproduction Guide

## Repository and prerequisites

- Repository: `https://github.com/Vaibhavsahkk/Proof_Before_Pay.git`
- Docker Desktop or Docker Engine with Docker Compose v2
- Git
- PowerShell on Windows
- Git Bash or Bash for `verify.sh`
- Approximate Phase 1 verification runtime: 1-2 minutes after dependencies are available
- API/service cost for Phases 0 and 1: $0

No model API or `GEMINI_API_KEY` is required for Phase 0 or Phase 1.

## Tested toolchain

Observed on the Windows verification host on 2026-08-29:

- Git `2.54.0.windows.1`
- Docker CLI and server `29.6.2`
- Docker Compose `v5.3.1`
- PowerShell `7.6.4`
- Git Bash `5.3.9(1)-release`
- Container Python `3.12.x`, pinned through the Docker base-image digest

These are recorded tested versions, not minimum-version claims. Native macOS/Linux execution remains unverified.

## Phase 0

Phase 0 was externally approved. Its tested candidate was `49358817c8481ca0bf3eaa6b5b1d2ddaa015cf96`; later commits store evidence and authorized Phase 1 work.

Run its retained checks with:

```powershell
.\scripts\run_adversarial_tests.ps1
.\verify.ps1
```

```bash
./verify.sh
```

## Phase 1 deterministic checks

The current tested Phase 1 candidate is `81258dab505429df34135a1fc72ea45527505510`.

Generate and validate the frozen benchmark artifacts:

```powershell
python scripts/generate_phase1_data.py
python scripts/generate_manifest.py
python scripts/validate_phase1.py
python scripts/verify_manifest.py
python -m pytest tests/test_phase1_validation.py tests/test_manifest.py -q
```

Expected focused result: 25 passed.

Run both complete Docker pipelines:

```powershell
.\verify.ps1
```

```bash
./verify.sh
```

Expected full result in each pipeline: 42 passed, followed by `ALL VERIFICATION STEPS PASSED`.

## Fresh-clone reproduction

From the main workspace, execute the exact candidate SHA:

```powershell
.\scripts\run_clean_clone_tests.ps1 -CandidateSha "81258dab505429df34135a1fc72ea45527505510" -Phase "phase_1"
```

Expected result: `CLEAN CLONE HARNESS RESULT: PASS` and process exit 0. The harness first proves fail-closed behavior with a harmless forced failure, clones into a unique `%TEMP%` path, runs the strict validator, manifest verifier, focused suite, both Docker pipelines, Git hygiene checks, and clean-status check. It then removes only its exact Compose project and exact temporary clone.

Current raw evidence: `evidence/phase_1/final_clean_clone_execution.txt`.

Do not run global Docker prune commands for this workflow.
