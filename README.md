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

The current repository implements the benchmark, deterministic oracle, validation, evidence, and isolated runtime/verifier infrastructure, and will now implement the fair baseline.

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

No model API or API key is required for Phase 0 or Phase 1.

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

Expected full result for each verified pipeline: 46 tests pass, followed by `ALL VERIFICATION STEPS PASSED`. The pipelines also validate schemas, oracle results, the frozen manifest, smoke execution, runtime inputs, non-root execution, and ground-truth/evaluator isolation.

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

Historical files prefixed with `superseded_` are retained for audit history and are not current decision evidence.

## Development Mode

For local live-code editing:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Do not use global Docker prune commands for this project workflow.
