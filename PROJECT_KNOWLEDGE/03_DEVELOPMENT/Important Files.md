# Important Files

## Main Project Definitions
- `docs/SOURCE_OF_TRUTH.md`: Authority hierarchy for conflicting project information.
- `sources/official_micro1_hackathon.pdf`: Official rules, judging criteria, ground rules, and deliverables.
- `sources/Idea to work.txt`: Original candidate problem pool.
- `docs/LOCKED_PROBLEM.md`: Locked problem, user, solution, and hard boundaries.
- `PLAN.md`: The master phase-gated plan outlining all 10 phases.
- `STATUS.md`: Tracking the current status, verification state, and phase lock/unlock.
- `README.md`: General project overview, rules, and verification setup.
- `DECISIONS.md`: Log of core architectural and process decisions.
- `REPRODUCE.md`: Reproducibility instructions for validators.

## Phase 1 Documentation
- `docs/PHASE_1_SCOPE.md`: The boundary constraints and workflow scope.
- `benchmark/RULEBOOK.md`: The rules by which the deterministic oracle processes invoice exceptions.
- `eval/EVAL_DESIGN.md`: The fair evaluation design criteria.

## Verification Pipelines
- `verify.ps1`: Windows-based Docker test pipeline.
- `verify.sh`: POSIX-based Docker test pipeline.
- `scripts/run_clean_clone_tests.ps1`: Harness for testing candidate commits in an isolated temporary clone.

## Phase 1 Scripts and Data
- `scripts/generate_phase1_data.py`: Generates the JSON schemas and synthetic benchmark cases.
- `scripts/validate_phase1.py`: The ground truth oracle that deterministically evaluates cases according to `RULEBOOK.md`.
- `scripts/generate_manifest.py`: Computes the SHA-256 manifest of the frozen benchmark.
- `scripts/verify_container_security.sh`: Checks inside the container to prevent path/data leakage.

## Benchmark Data
- `data/cases/public/*.json`: Public case inputs provided to agents.
- `data/cases/ground_truth/*.json`: Hidden ground-truth expected outcomes.
- `benchmark/schemas/*.json`: Schemas for public data, ground truth, and output contract.

## Current Evidence
- `evidence/phase_1/final_clean_clone_execution.txt`: Current clean-clone execution evidence for the tested Phase 1 candidate.
- `evidence/phase_1/SHA256_MANIFEST.txt`: Frozen benchmark integrity manifest.
- `reports/phase_1_review_packet.md`: Phase 1 external-review packet.
