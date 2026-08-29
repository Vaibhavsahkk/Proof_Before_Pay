# Reproduction Guide

## Repository and prerequisites

- Repository: `https://github.com/Vaibhavsahkk/Proof_Before_Pay.git`
- Docker Desktop or Docker Engine with Docker Compose v2
- Git
- PowerShell on Windows
- Git Bash for the verified Windows `verify.sh` run; native macOS/Linux Bash remains unverified
- Approximate Phase 1 verification runtime: 1-2 minutes after dependencies are available
- API/service cost for Phases 0 and 1: $0

No model API or `GEMINI_API_KEY` is required for Phase 0, Phase 1, or Phase 2 scaffold verification.

## Tested toolchain

Observed on the Windows verification host on 2026-08-29:

- Git `2.54.0.windows.1`
- Docker CLI and server `29.6.2`
- Docker Compose `v5.3.1`
- PowerShell `7.6.4`
- Git Bash `5.3.9(1)-release`
- Container Python `3.12.x`, pinned through the Docker base-image digest

These are recorded tested versions, not minimum-version claims. Native macOS/Linux execution remains unverified.

On this Windows host, a bare `bash` command launched from PowerShell resolves to WSL, not Git Bash. Either run `./verify.sh` from an already-open Git Bash shell or invoke the verified executable explicitly:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' ./verify.sh
```

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

Phase 1 was externally approved. The tested candidate was `43ba9356aaa110113e81a446cb701bee40f0fc39`.

Generate and validate the frozen benchmark artifacts:

```powershell
python scripts/generate_phase1_data.py
python scripts/generate_manifest.py
python scripts/validate_phase1.py
python scripts/verify_manifest.py
python -m pytest tests/test_phase1_validation.py tests/test_manifest.py -q
```

Expected focused result: 29 passed.

Run both complete Docker pipelines:

```powershell
.\verify.ps1
```

```bash
./verify.sh
```

Expected full result in each pipeline: 46 passed, followed by `ALL VERIFICATION STEPS PASSED`. Each pipeline also proves that the runtime contains required public inputs, excludes evaluator/ground-truth artifacts, and rejects an injected ground-truth mount with scanner exit 1.

## Fresh-clone reproduction

From the main workspace, execute the exact candidate SHA:

```powershell
.\scripts\run_clean_clone_tests.ps1 -CandidateSha "43ba9356aaa110113e81a446cb701bee40f0fc39" -Phase "phase_1"
```

Expected result: `CLEAN CLONE HARNESS RESULT: PASS` and process exit 0. The harness first proves fail-closed behavior with a harmless forced failure, clones into a unique `%TEMP%` path, runs the strict validator, manifest verifier, focused suite, both Docker pipelines, Git hygiene checks, and clean-status check. It then removes only its exact Compose project and exact temporary clone.

Current raw evidence: `evidence/phase_1/final_clean_clone_execution.txt`.

## Phase 2 API-independent verification

These commands do not call Gemini:

```powershell
python -m pytest -q tests/test_phase2_baseline.py
python scripts/verify_manifest.py
.\verify.ps1
& 'C:\Program Files\Git\bin\bash.exe' ./verify.sh
```

Run the exact remote clean-clone scaffold gate with:

```powershell
.\scripts\run_clean_clone_tests.ps1 -CandidateSha "eac35cdb4994f917d76cde4a6ca1749957d65f3f" -Phase "phase_2"
```

Expected result: `CLEAN CLONE HARNESS RESULT: PASS` and exit 0. This gate verifies the candidate commit, frozen manifest, 29 focused Phase 2 tests, the exact missing-key rejection, both 75-test Docker pipelines, clean post-test Git state, and exact-project cleanup. Its current evidence is the normalized machine-captured log `evidence/phase_2/scaffold_clean_clone_execution.txt` with SHA-256 `71F2DFE5230C36F5C6F93E107BF2E5E01F65C549D8ACF6B85C3B89D784E32483`; it is not represented as byte-for-byte terminal capture.

The actual baseline remains NOT RUN until the scaffold is independently accepted and a human supplies `GEMINI_API_KEY` through a local environment variable. Never paste the key into chat, source files, logs, or evidence.

Do not run global Docker prune commands for this workflow.
