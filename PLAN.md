# MASTER PHASE-GATED PLAN

## Roles

### Human
Final authority for secrets, permissions, machine actions, external accounts, paid services, and consequential decisions.

### Antigravity
Executor. Must read the source-of-truth files, inspect before changing, run real commands, preserve evidence, and stop when blocked.

### Local ChatGPT
Monitor. Checks every material step for phase scope, evidence quality, safety, benchmark integrity, and unsupported assumptions. It can STOP but cannot approve.

### External ChatGPT
Senior mentor and final gatekeeper. Reviews the phase packet and either approves with `PHASE APPROVED — 100%` or returns `PHASE FAIL` with exact remediation.

---

# PHASE 0 — ENVIRONMENT & GOVERNANCE

### Goal
Create a clean, isolated, reproducible workspace.

### Must exist
- governance files
- source-of-truth hierarchy
- environment/dependency files
- container setup
- trace/audit structure
- basic tests for any utilities introduced in Phase 0

### Required evidence
- dependency install
- container config validation
- clean build
- smoke run
- automated tests
- security/image inspection where containerized
- sanitized trace example

### Exit criteria
All Phase 0 acceptance criteria pass and external ChatGPT approves.

---

# PHASE 1 — PROBLEM SCOPE & BENCHMARK DESIGN

### Goal
Turn the locked problem into a precise testable workflow.

### Define
- exact target user
- supported evidence types
- anomaly taxonomy
- output contract
- safety boundaries
- benchmark schema
- ground-truth rules

### Build
Start with 5 cases. Do not scale until the 5-case design is valid.

### Exit criteria
Each case has independently verified ground truth; benchmark is reproducible; evaluator cannot access hidden ground truth through agent inputs.

---

# PHASE 2 — FAIR BASELINE

### Goal
Run a reasonable simple baseline on the same cases.

### Record
- model/provider/version
- exact prompt
- tool access
- settings
- raw outputs
- evaluator outputs
- runtime/cost where available

### Exit criteria
No simulated or hand-written performance numbers. Results are reproducible from frozen inputs.

---

# PHASE 3 — FAILURE ANALYSIS

### Goal
Use observed baseline failures to justify every agent capability.

### Exit criteria
Every advanced capability maps to an observed failure or explicit requirement. No complexity is added “because it sounds agentic.”

---

# PHASE 4 — MINIMAL AGENT V1

### Goal
Build the smallest useful agentic workflow.

Likely shape:
INGEST → EXTRACT → RECONCILE → DETERMINISTIC CHECKS → VERIFY → REPORT

Add tools only when justified by Phase 3.

---

# PHASE 5 — MEMORY / HISTORY / HUMAN REVIEW

Add only evidence-backed capabilities such as vendor alias memory, prior transaction history, uncertainty handling, and human review checkpoints.

No automatic payment execution.

---

# PHASE 6 — SECURITY & SANDBOX

Prove the system cannot access secrets, escape intended boundaries, or execute consequential payment actions.

Minimum checks:
- safe mounts
- credential isolation
- bounded tool calls
- timeout/resource limits
- trace sanitization
- no payment execution

---

# PHASE 7 — FINAL EVALUATION

Freeze benchmark first.

Run baseline and final agent on exactly the same cases.

Choose ONE primary user-success metric before final scoring.

Report per-case results, failures, false positives, financial-calculation accuracy, evidence attribution, and improvement delta.

---

# PHASE 8 — IMPROVEMENT CHANGELOG & HOT TAKE

Document only real experiments:
Baseline → Iteration 1 → Iteration 2 → Final.

Every entry needs:
- what changed
- why
- evidence
- result
- decision

---

# PHASE 9 — SUBMISSION ENGINEERING

Prepare:
- complete code
- README
- reproduction guide
- improvement changelog
- trajectories
- evaluation report
- <=5-minute video
- security notes
- no secrets

The video must show the problem, baseline, one realistic execution, final comparison, and changelog.

---

# PHASE 10 — FINAL SUBMISSION AUDIT

Run from a clean environment.

Verify:
- setup
- baseline
- final solution
- evaluation
- frozen benchmark
- trajectories
- documentation
- security
- all official deliverables

Only external ChatGPT may authorize submission.
