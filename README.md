# micro1 Frontier Engineering Challenge 2026 - Phase 0 Scaffold

This repository contains the Phase 0 (Pre-Kickoff) infrastructure scaffold for the micro1 Frontier Engineering Challenge 2026.

> **STATEMENT**: The challenge problem statement is still unavailable (unlocks August 28). This repository contains strictly un-opinionated backend orchestration, security, and verification infrastructure to satisfy the stringent requirements for safety, telemetry, and isolation. No challenge-specific code is implemented yet.

## Prerequisites

- **Docker Engine** (with Docker Compose v2)
- **Git**

No host Python, virtual environment, or global packages are required. The entire verification pipeline is Docker-driven.

## Verification Workflow (Clean Environment)

The `verify.ps1` (PowerShell) and `verify.sh` (POSIX) scripts execute a rigorous 6-step assertion pipeline entirely orchestrated via Docker.

### Exact Verification Command

**Windows (PowerShell):**
```powershell
.\verify.ps1
```

**macOS/Linux (POSIX):**
```bash
./verify.sh
```

### Expected Result

The verifier will dynamically ensure no untracked secrets are present, build the verification image from scratch, run the local adversarial test suite *inside* the fresh container, validate strictly that the default compose configuration has zero host bind mounts, run the smoke execution, and perform a recursive container-level security assertion.

Expected final output:
```
************************************************************
ALL VERIFICATION STEPS PASSED
************************************************************
```

## Development Mode Workflow

The default `docker-compose.yml` ensures absolute production isolation and contains NO host bind mounts.

For local development (live code editing), you must explicitly overlay the development configuration `docker-compose.dev.yml`, which mounts `./src` and `./tests` as read-only, and `./traces` as writable.

### Development-Mode Command
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```
*Note: Always use `-f docker-compose.yml -f docker-compose.dev.yml` to ensure development mounts are actively appended to the production configuration.*

## Troubleshooting

- **Missing Docker/Git:** The verification scripts check for the `docker` and `git` binaries in your system `PATH`. If they fail, install Docker Desktop (Windows/Mac) or Docker Engine (Linux), and install Git.
- **Permission Errors:** Ensure your user has permissions to run Docker commands, or run the POSIX verification script with appropriate privileges.
