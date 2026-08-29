# Phase 1 External Review Packet

## Gate request

Current phase: Phase 1 - Problem Scope & Benchmark Design.

Requested verdict: External ChatGPT must return exactly either `PHASE APPROVED — 100%` or `PHASE FAIL`.

Local gate result: `READY FOR EXTERNAL CHATGPT REVIEW`.

Phase 2 remains unauthorized until the exact approval verdict is received.

## Tested source state

- Repository: `https://github.com/Vaibhavsahkk/Proof_Before_Pay.git`
- Tested candidate commit: `43ba9356aaa110113e81a446cb701bee40f0fc39`
- Candidate commit check: `git show --check 43ba9356aaa110113e81a446cb701bee40f0fc39` exited 0.
- Candidate was pushed before clean-clone verification.
- Final evidence/docs commit and remote equality are recorded in the detached final provenance packet generated after this tracked packet is committed.

## Acceptance criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Exact target user and workflow boundary | PASS | `docs/PHASE_1_SCOPE.md` |
| Safety boundaries | PASS | `docs/PHASE_1_SCOPE.md`, `docs/LOCKED_PROBLEM.md` |
| Strict versioned JSON schemas | PASS | `benchmark/schemas/*.json`; strict validator exit 0 |
| Deterministic anomaly taxonomy and precedence | PASS | `benchmark/RULEBOOK.md`; oracle tests |
| Six synthetic benchmark cases | PASS | `data/cases/public/`, `data/cases/ground_truth/` |
| Neutral public filenames and case IDs | PASS | `case_001` through `case_006`; leakage tests |
| No answer leakage in public input | PASS | real-bundle validation plus adversarial value, key, filename/path, and case-ID tests |
| Independent deterministic ground truth | PASS | six-case oracle matrix below |
| Frozen benchmark integrity | PASS | SHA-256 manifest verifier and mutation tests |
| Fair evaluation design | PASS | `eval/EVAL_DESIGN.md` |
| Clean-clone reproducibility | PASS | `evidence/phase_1/final_clean_clone_execution.txt` |
| Fail-closed harness and bounded cleanup | PASS | forced inner exit 7 produced harness exit 1; exact Compose project cleanup verified empty |
| Phase boundary | PASS | no Phase 2 baseline or agent implementation |

## Observed command results

| Command/check | Observed result |
| --- | --- |
| `python scripts/validate_phase1.py` | exit 0; all six cases matched ground truth |
| `python scripts/verify_manifest.py` | exit 0 |
| Focused Phase 1 pytest suite | exit 0; 29 passed |
| `.\verify.ps1` in clean clone | exit 0; 46 passed; injected ground truth rejected with scanner exit 1 |
| `bash ./verify.sh` in clean clone | exit 0; 46 passed; injected ground truth rejected with scanner exit 1 |
| Harness forced-failure self-test | inner exit 7; harness exit 1; expected rejection |
| `git diff --check` in clean clone | exit 0 |
| `git diff --cached --check` in clean clone | exit 0 |
| `git status --short` in clean clone | exit 0; empty output |
| Exact-project Compose cleanup | exit 0; no matching containers or networks remained |
| Exact temporary clone cleanup | PASS; path absent after cleanup |

## Six-case ground-truth matrix

| Case ID | Deterministically derived | Frozen ground truth | Result |
| --- | --- | --- | --- |
| `case_001` | PAY | PAY | PASS |
| `case_002` | HOLD - Duplicate Billing | HOLD - Duplicate Billing | PASS |
| `case_003` | HOLD - Quantity Mismatch | HOLD - Quantity Mismatch | PASS |
| `case_004` | HOLD - Price Contradiction | HOLD - Price Contradiction | PASS |
| `case_005` | INVESTIGATE - Unverified Bank Change | INVESTIGATE - Unverified Bank Change | PASS |
| `case_006` | HOLD - Duplicate Billing, Unverified Bank Change | HOLD - Duplicate Billing, Unverified Bank Change | PASS |

## Integrity hashes

- `evidence/phase_1/SHA256_MANIFEST.txt` exact Git-blob/archive SHA-256: `EEF0BDF46D385F9BC47E14AF4E188DACE2B2E03B9510793E62D04706E03DAABE`
- `evidence/phase_1/final_clean_clone_execution.txt` SHA-256: `218247B6DD0DCF1AE35614348396208CE8732022FB65B3C9FAB48A54112F195B`
- The Windows working-tree copy of `SHA256_MANIFEST.txt` uses CRLF and hashes to `01AD1525F5D7F16416FC62C8B348A719268DE6AF5136FEA5E80A82D7741419E4`; that host-specific hash is not the immutable Git/archive provenance hash.
- The manifest lists every benchmark schema, public case, hidden ground-truth case, and the rulebook. Missing, extra, duplicate, malformed, or hash-mismatched entries fail verification.

## Evidence provenance

- Current decision evidence: `evidence/phase_1/final_clean_clone_execution.txt`.
- Benchmark manifest: `evidence/phase_1/SHA256_MANIFEST.txt`.
- `evidence/phase_1/superseded_clean_clone_execution_a2fe2dc.txt` is retained historical output. It predates strict schema execution and is not decision evidence.
- `evidence/phase_1/superseded_local_execution_a2fe2dc.txt` is retained historical output and is not decision evidence.

## Correction and safety history

- An earlier executor attempt used an out-of-scope global Docker container cleanup command. The monitor stopped that run and accepts none of its claimed results.
- The replacement harness uses one unique Compose project, runs `down --remove-orphans` only for that exact project, verifies no matching containers or networks remain, and removes only its GUID-named `%TEMP%` clone.
- Earlier commits failed `git show --check`; corrective candidate `43ba9356aaa110113e81a446cb701bee40f0fc39` passes.

## Exact Phase 1 changed files

- `DECISIONS.md`
- `Dockerfile`
- `REPRODUCE.md`
- `STATUS.md`
- `benchmark/README.md`
- `benchmark/RULEBOOK.md`
- `benchmark/schemas/ground_truth.json`
- `benchmark/schemas/output_contract.json`
- `benchmark/schemas/public_evidence_bundle.json`
- `data/cases/ground_truth/case_001.json`
- `data/cases/ground_truth/case_002.json`
- `data/cases/ground_truth/case_003.json`
- `data/cases/ground_truth/case_004.json`
- `data/cases/ground_truth/case_005.json`
- `data/cases/ground_truth/case_006.json`
- `data/cases/public/case_001.json`
- `data/cases/public/case_002.json`
- `data/cases/public/case_003.json`
- `data/cases/public/case_004.json`
- `data/cases/public/case_005.json`
- `data/cases/public/case_006.json`
- `docker-compose.yml`
- `docs/PHASE_1_SCOPE.md`
- `eval/EVAL_DESIGN.md`
- `evidence/phase_1/SHA256_MANIFEST.txt`
- `evidence/phase_1/final_clean_clone_execution.txt`
- `evidence/phase_1/superseded_clean_clone_execution_a2fe2dc.txt`
- `evidence/phase_1/superseded_local_execution_a2fe2dc.txt`
- `reports/phase_1_review_packet.md`
- `requirements-dev.txt`
- `scratch/run_clean_clone.ps1`
- `scripts/generate_manifest.py`
- `scripts/generate_phase1_data.py`
- `scripts/run_clean_clone_tests.ps1`
- `scripts/validate_phase1.py`
- `scripts/verify_container_security.sh`
- `scripts/verify_manifest.py`
- `tests/test_manifest.py`
- `tests/test_phase1_validation.py`
- `verify.ps1`
- `verify.sh`

## Assumptions

- The Phase 2 evaluator will expose only public case bundles to the baseline/agent and will keep ground truth outside their accessible filesystem.
- PAY, HOLD, and INVESTIGATE remain recommendations; a human makes the final decision.

## Risks

- Native macOS/Linux execution is unverified; Git Bash on Windows is the observed POSIX-like environment.
- No vulnerability/CVE scanner was run, and no vulnerability-remediation claim is made.
- The benchmark currently contains six cases by explicit Phase 1 plan; scaling is deferred until the design is approved.

## Failures

None in the accepted candidate run. Historical failed or superseded evidence is retained and labeled.

## Blockers

None.

## Human action required

None.

READY FOR EXTERNAL CHATGPT REVIEW
