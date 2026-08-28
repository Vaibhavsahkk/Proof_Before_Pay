# micro1 Agentic Workflows Hackathon 2026 — Phase 0 Scaffold

## Project

**Evidence-Driven Pre-Payment Exception Investigator for Small Businesses**

An agentic investigator gathers and reconciles evidence from supplier invoices, purchase orders, goods receipt records, and vendor master records. It produces an evidence-linked PAY / HOLD / INVESTIGATE recommendation for a human reviewer.

Hard boundaries:
- No payment is ever executed.
- No bank details are changed.
- No supplier is declared definitely fraudulent.
- The human makes all consequential decisions.

**Current phase:** Phase 0 — Environment & Governance only.

No challenge-specific agent code is implemented yet.

## Prerequisites

- **Docker Engine** (with Docker Compose v2)
- **Git**

No host Python, virtual environment, or global packages are required. The entire verification pipeline is Docker-driven.

## Verification

The `verify.ps1` (PowerShell) and `verify.sh` (POSIX) scripts execute a 6-step assertion pipeline orchestrated via Docker:

1. Git tracked-traces check (fails immediately if git is not available or not a repository)
2. Compose isolation check (fails if host bind mounts or API keys appear in resolved config)
3. Docker build (no-cache, pinned digest)
4. Test suite (16 tests inside container)
5. Smoke execution
6. Container security assertion (filename-based scan inside the container filesystem)

> **Note:** The security assertion inspects filenames inside the container only. It does not scan untracked host files.

### Windows (PowerShell) — VERIFIED
```powershell
.\verify.ps1
```
The verification pipeline succeeds. See `evidence/phase_0/pipeline_execution.txt`.

### POSIX (macOS/Linux or Git Bash) — VERIFIED
```bash
./verify.sh
```
The complete Git Bash pipeline passed with exit 0 and 16 tests passing. It is recorded as Test L in `evidence/phase_0/adversarial_execution.txt`.

### Clean-Clone Reproduction — UNVERIFIED
No remote repository URL exists. `git remote -v` returns no entries.

### Expected Successful Final Output
```
************************************************************
ALL VERIFICATION STEPS PASSED
************************************************************
```

## Development Mode

For local development (live code editing), overlay the development configuration:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Troubleshooting

- **Missing Docker/Git:** Verification scripts check for `docker` and `git` in PATH. Install Docker Desktop (Windows/Mac) or Docker Engine (Linux) and Git.
- **Permission Errors:** Ensure your user has permission to run Docker commands.
