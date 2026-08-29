# Proof Before Pay

Evidence-Driven Pre-Payment Exception Investigator for Small Businesses, built for the micro1 Agentic Workflows Hackathon 2026.

The intended workflow reconciles supplier invoices, purchase orders, goods-receipt records, vendor-master records, prior-payment history, and bank-change evidence. It will produce an evidence-linked `PAY`, `HOLD`, or `INVESTIGATE` recommendation for a human reviewer.

## Safety Boundaries

- AI reasons over evidence.
- Deterministic tools calculate.
- A human makes every consequential decision.
- No payment execution.
- No real bank-detail changes or payment instructions.
- No definitive declaration that a supplier is fraudulent.
- No private real-world financial data in the repository.

## Current Phase

Phase 1 is externally approved.

Phase 2 - Fair Baseline - is the only active phase. Phase 3+ remains locked.

The repository contains the frozen benchmark, a verified Phase 2 baseline/evaluator, and a valid six-case Gemini baseline run. Phase 2 received an external `PHASE FAIL` verdict and is ACTIVE in remediation.

## Source of Truth

Read `docs/SOURCE_OF_TRUTH.md` first. It prioritizes the official hackathon PDF, original candidate pool, locked problem, and current executable repository state. Research under `sources/` is advisory unless explicitly promoted through an approved decision.

## Phase 1 Benchmark

- 6 synthetic public cases with matching hidden ground truth.
- Strict JSON schemas and neutral case identifiers.
- Exact-USD scope and deterministic Decimal calculations.
- HOLD > INVESTIGATE > PAY recommendation precedence.
- Primary metric: exact case-level recommendation accuracy.
- Safety guardrail: Unsafe-PAY rate.
- Frozen SHA-256 benchmark manifest.

The Dockerfile uses separate targets:

- `runtime`: application code, public cases, public contracts, rulebook, and security scanner only.
- `verifier`: tests, evaluator scripts, schemas, manifest, and hidden ground truth.

## Prerequisites

- Docker Desktop or Docker Engine with Docker Compose v2.
- Git.
- PowerShell on Windows.
- Git Bash for the verified Windows POSIX-like pipeline.

No model API or API key is required for Phase 0, Phase 1, or offline verification of the committed Phase 2 evidence. Re-running the provider baseline requires `GEMINI_API_KEY` supplied only through the local process environment.

## Verification

PowerShell:

```powershell
.\verify.ps1
```

Git Bash, when already inside a Git Bash shell:

```bash
./verify.sh
```

From PowerShell, explicitly invoke Git Bash to avoid accidentally selecting WSL:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' ./verify.sh
```

The full result is accepted only when every collected test passes, the command exits 0, and `ALL VERIFICATION STEPS PASSED` is printed. The pipelines also validate schemas, oracle results, the frozen manifest, smoke execution, runtime inputs, non-root execution, credential isolation, and ground-truth/evaluator isolation.

Focused deterministic checks:

```powershell
python scripts/validate_phase1.py
python scripts/verify_manifest.py
python -m pytest tests/test_phase1_validation.py tests/test_manifest.py -q
```

Expected focused result: 29 tests pass.

See `REPRODUCE.md` for the clean-clone workflow and tested toolchain. Native macOS/Linux execution and vulnerability/CVE scanning remain unverified.

## Current Evidence

- `evidence/phase_1/final_clean_clone_execution.txt`
- `evidence/phase_1/SHA256_MANIFEST.txt`
- `reports/phase_1_review_packet.md`
- `evidence/phase_2/runs/run_20260829_154058_02e9416b/`
- `evidence/phase_2/final_clean_clone_execution.txt`
- `reports/phase_2_review_packet.md`

Historical files prefixed with `superseded_` are retained for audit history and are not current decision evidence.

The accepted Phase 2 run is `evidence/phase_2/runs/run_20260829_154058_02e9416b`. It records six successful `gemini-3.6-flash` responses, 100% exact recommendation and findings correctness, 100% schema validity, and 0/5 unsafe PAY recommendations. These are six-case synthetic benchmark results, not production-performance claims. See `reports/phase_2_review_packet.md` for provenance, limitations, and the clean-clone gate.

## Development Mode

For local live-code editing:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Do not use global Docker prune commands for this project workflow.
