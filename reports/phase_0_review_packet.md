# Phase 0 Review Packet

## Gate state

Current phase: Phase 0 — Environment & Governance.

Result: **NOT READY FOR EXTERNAL CHATGPT REVIEW**. Docker-backed Windows and POSIX validation now pass with current evidence. Clean-clone reproduction remains unverified because no repository URL is configured. Phase 1 remains unauthorized.

## Corrections implemented

- `verify.ps1` and `verify.sh` now allow only `traces/README.md`, `traces/sanitized/**`, `trajectories/README.md`, and `trajectories/sanitized/**`; tracked `raw/README.md` paths are rejected.
- Both verification scripts fail closed when `git ls-files` fails.
- `scripts/verify_container_security.sh` uses one fail-closed `find` command, rejects exact raw trace/trajectory directories and contents, supports paths with spaces, permits non-matching lookalikes, and rejects UID 0.
- `scripts/run_adversarial_tests.ps1` captures real child-process exits, restores all sentinel environment variables, writes normalized UTF-8/LF evidence, removes its newly created temporary repositories, and records hashes plus Git state.
- `.gitattributes` fixes LF endings for shell scripts, PowerShell scripts, and Phase 0 text evidence.
- `src/utils/human_checkpoint.py` no longer silently hides an audit-log failure after unsafe approval text is rejected; it reports the failure and remains fail-closed.
- `tests/test_human_checkpoint.py` adds a regression test for that audit-log failure path. The current test count is 16.
- Gemini remains a conditional later-phase provider only. No model API is required or authorized in Phase 0, and no API key is forwarded through Compose.
- Modified `verify.sh` and `verify.ps1` to use a relative path (`./scripts/verify_container_security.sh`) to prevent MSYS2 path conversion issues inside Git Bash.

## Commands actually run in the current correction pass

| Command/check | Observed result |
|---|---|
| PowerShell parser on `verify.ps1` and adversarial harness | PASS, 0 parser errors |
| `git diff --check` on current worktree | PASS, exit 0 |
| `bash -n ./verify.sh` | PASS, exit 0 using Git Bash |
| `bash -n ./scripts/verify_container_security.sh` | PASS, exit 0 using Git Bash |
| PowerShell Git negative-path harness test | PASS, verifier process exit 128 |
| PowerShell rejection of tracked `traces/raw/README.md` | PASS, verifier exit 1 before Compose |
| PowerShell rejection of tracked `trajectories/raw/README.md` | PASS, verifier exit 1 before Compose |
| Compose three-provider sentinel test | PASS, Compose exit 0; names/values absent; environment restored |
| POSIX Git negative-path harness test | PASS, non-zero exit before Compose |
| Manual unsafe-UI/audit-write failure check | PASS; action returned `False` and audit error was reported |
| Adversarial harness overall | PASS, exit 0; build precondition and Tests A-L passed |
| Current `verify.ps1` pipeline | PASS, exit 0 |
| Current 16-test suite | PASS, exit 0 |
| Full `verify.sh` pipeline | PASS, exit 0; 16 tests passed in 0.15s as Test L |
| Clean-clone reproduction | UNVERIFIED |
| Explicit `git add` of reviewed files | PASS, exit 0 |
| Staged diff `git diff --cached --check` | PASS, exit 0 |

## Current raw evidence

- `evidence/phase_0/adversarial_execution.txt`: current harness output. Current-image build and Tests A-L pass; harness exit 0.
- `evidence/phase_0/pipeline_execution.txt`: current Windows pipeline attempt. Git, Compose, Docker Build, Pytest, and Security scan all pass; process exit 0.

## Assumptions

- No Gemini API is needed during Phase 0.
- A human will choose and authorize the repository remote.

## Risks

- No vulnerability/CVE scanner was run, and no remediation claim is made.
- Clean-clone reproduction is unverified.

## Blockers and required human actions

1. Provide the intended repository URL, then perform clean-clone reproduction.

**STOPPED — ISSUE FOUND**
