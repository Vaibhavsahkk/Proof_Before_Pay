# Reproduction Guide

## Repository and prerequisites

- Repository: `https://github.com/Vaibhavsahkk/Proof_Before_Pay.git`
- Docker Desktop or Docker Engine with Docker Compose v2
- Git
- PowerShell on Windows
- Git Bash for the verified Windows `verify.sh` run; native macOS/Linux Bash remains unverified
- Approximate Phase 1 verification runtime: 1-2 minutes after dependencies are available
- API/service cost for Phases 0 and 1: $0

No model API or `GEMINI_API_KEY` is required for Phase 0, Phase 1, or offline verification of the committed Phase 2 evidence.

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

Expected full result in each pipeline: all collected tests pass (the count has
grown with the project: 46 at Phase 1 freeze, 81 at Phase 2, 135 at Phase 4.8,
165 collected at the 2026-09-01 audit — check the verifier image output for
the exact current number), followed by `ALL VERIFICATION STEPS PASSED`. Each
pipeline also proves that the runtime contains required public inputs,
excludes evaluator/ground-truth artifacts, and rejects an injected
ground-truth mount with scanner exit 1.

Note (2026-09-01 audit): `tests/test_environment.py` runs only inside the
Linux Docker container by design; `tests/test_ui_e2e_integration.py` and the
pipeline tests in `tests/test_ui.py` call the live Gemini API for uncached
cases and require `GEMINI_API_KEY` with available quota. The offline suite
(`python -m pytest --ignore=tests/test_environment.py --ignore=tests/test_ui_e2e_integration.py --ignore=tests/test_ui.py -q`)
passed 144/144 on this host and from a fresh git-archive clone.

## Fresh-clone reproduction

From the main workspace, execute the exact candidate SHA:

```powershell
.\scripts\run_clean_clone_tests.ps1 -CandidateSha "43ba9356aaa110113e81a446cb701bee40f0fc39" -Phase "phase_1"
```

Expected result: `CLEAN CLONE HARNESS RESULT: PASS` and process exit 0. The harness first proves fail-closed behavior with a harmless forced failure, clones into a unique `%TEMP%` path, runs the strict validator, manifest verifier, focused suite, both Docker pipelines, Git hygiene checks, and clean-status check. It then removes only its exact Compose project and exact temporary clone.

Current raw evidence: `evidence/phase_1/final_clean_clone_execution.txt`.

## Phase 2 verification

These commands do not call Gemini:

```powershell
python -m pytest -q tests/test_phase2_baseline.py
python scripts/verify_manifest.py
.\verify.ps1
& 'C:\Program Files\Git\bin\bash.exe' ./verify.sh
```

The current accepted candidate is verified with:

```powershell
.\scripts\run_clean_clone_tests.ps1 -CandidateSha "1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c" -Phase "phase_2"
```

Expected result: `CLEAN CLONE HARNESS RESULT: PASS` and exit 0. The gate verifies the candidate commit, frozen manifest, 35 focused Phase 2 tests, exact missing-key rejection, deterministic verification of the committed VALID report, both 81-test Docker pipelines, clean post-test Git state, and exact-project cleanup. Current normalized evidence is `evidence/phase_2/final_clean_clone_execution.txt`, SHA-256 `D720522023C2ACBB17399E1F47A976FD2894FBBD1E4E3AD761518E5E159D2D15`.

Verify the accepted report offline, without an API key:

```powershell
python -m eval.evaluate_baseline evidence/phase_2/runs/run_20260830_091031_f1cc354c --verify-existing
```

To generate a new provider run, first ensure the repository is clean and set `GEMINI_API_KEY` only in the local process environment, then run:

```powershell
python -m baseline.run_baseline
python -m eval.evaluate_baseline evidence/phase_2/runs/<new_run_id>
```

The accepted run is pinned to `gemini-3.6-flash`. The two provider failures and the CRLF-dependent v1 run are preserved but excluded from decision metrics. Never paste the API key into chat, source files, logs, or evidence.

Do not run global Docker prune commands for this workflow.

## Phase 4.3 Demo Hardening and Reproducibility

The final end-to-end agentic workflow is invoked via the `src.main` entry point. It requires `GEMINI_API_KEY` to be set in the local environment and executes the Orchestrator over the specified AP evidence bundle.

### Running the Demo

To run a specific evidence bundle, use the `--file` flag:

```powershell
python -m src.main --file data/cases/public/case_001.json
```

Or on Linux/Git Bash:

```bash
python -m src.main --file data/cases/public/case_001.json
```

The output provides a structured, human-readable review panel, clearly summarizing extracted facts, identified anomalies, execution traces, and the automated "Demo Mode Action" (which translates the agent's final decision into a workflow action such as proceeding with automated clearing or halting for human review).

### Traces and Auditing

Every run generates a secure trace file (e.g., `traces/raw/trace_*.jsonl`). These traces are scrubbed of any sensitive information (e.g., API keys) and contain a detailed, step-by-step audit of the LLM interactions and deterministic tool outputs used during the run.

### Testing Phase 4

Verify the final implementation regressions and end-to-end functionality via:

```powershell
python -m pytest tests/test_phase4_1_e2e.py -v
```
