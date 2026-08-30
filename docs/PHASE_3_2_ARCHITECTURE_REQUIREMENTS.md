# Phase 3.2 Agent Opportunity & Architecture Requirements

## 1. Objective
Convert the verified Phase 3.1 baseline analysis into a precise, defensible architecture REQUIREMENTS specification for the future agentic system.

## 2. Problem Boundary
**Evidence-Driven Pre-Payment Exception Investigator for Small Businesses.**
- **Scope:** Investigate supplier-payment exceptions using evidence (invoice, PO, GRN, vendor master, bank-change, history).
- **Output:** Recommendation of PAY, HOLD, or INVESTIGATE.
- **Constraints:** The system must never autonomously execute a payment. The final consequential decision remains with a human.

## 3. Agent Responsibility
**INPUT → REASONING → TOOL USE → VERIFICATION → OUTPUT**
- **Responsible for:** Semantic mapping of incoming heterogeneous evidence; deciding which verification paths/tools are needed; identifying missing unstructured information; constructing explainable recommendations.
- **NOT responsible for:** Exact decimal math; exact string matching; final rulebook evaluation; executing payments.

## 4. Deterministic Responsibility
- **Responsible for:** Strict mathematical calculations (tax, subtotals, rounding to 0.01 tolerance); Exact string equality matching (vendor IDs, line IDs); Validating required JSON schemas; Aggregating anomalies strictly mapped to the RULEBOOK.md.
- **NOT responsible for:** Semantic interpretation of natural language fields or heterogeneous formats.

## 5. Component Responsibility Matrix

| Component | Responsibility | Deterministic/Agentic/Hybrid | Why |
|---|---|---|---|
| Evidence Ingestion | Parse and structure incoming documents | Deterministic | Schema validation must not hallucinate fields. |
| Field Extraction | Extract specific semantic data points | Hybrid | LLM understands natural language; Deterministic enforces schema constraints. |
| Exact Field Comparison | Compare IDs across PO, GRN, and Invoice | Deterministic | Strict exact equality requirement prevents fuzzy false positives. |
| Arithmetic Verification | Verify subtotals, tax, and line amounts | Deterministic | 0.01 tolerance `ROUND_HALF_UP` math requires a calculator, not an LLM. |
| Anomaly Detection | Map tool outcomes to rulebook conditions | Deterministic | Business logic precedence (HOLD > INVESTIGATE) must be strict. |
| Evidence Attribution | Trace findings back to source data | Hybrid | Agent identifies the citation, deterministic layer validates it exists. |
| Finding Completeness | Ensure all anomalies are checked before return | Deterministic | Prevents early short-circuiting on the first found anomaly. |
| Final Recommendation | Generate PAY/HOLD/INVESTIGATE | Deterministic | Strictly driven by the presence of anomalies per the rulebook. |
| Escalation Explanation| Generate human-readable summary of anomalies | Agentic | Humans need nuanced context for investigations. |
| Audit Logging | Persist the execution trace securely | Deterministic | Cannot be bypassed by agent hallucination. |

## 6. Tool Requirements
**Tool 1: Decimal Calculator**
- **Purpose:** Perform exact math for quantities, prices, taxes, and totals.
- **Input:** JSON array of operations (operands and operators).
- **Output:** Strict numerical result.
- **When Called:** When verifying any line-item total, subtotal, or tax calculation.
- **Must be Deterministic:** YES.
- **Failure Behavior:** Return calculation error; agent escalates.
- **Security Constraint:** Pure computation, no state modification.

**Tool 2: String Equality Checker**
- **Purpose:** Compare vendor IDs, line IDs, and names.
- **Input:** String A, String B.
- **Output:** Boolean.
- **When Called:** When validating PO/GRN matching or Vendor Master checks.
- **Must be Deterministic:** YES.
- **Failure Behavior:** Return boolean False; map to anomaly.
- **Security Constraint:** Read-only comparison.

**Tool 3: Rule Evaluator**
- **Purpose:** Map verified facts to the Rulebook exceptions.
- **Input:** List of verified mismatches or math errors.
- **Output:** List of formal findings and final recommendation (PAY/HOLD/INVESTIGATE).
- **When Called:** End of the orchestration loop.
- **Must be Deterministic:** YES.
- **Failure Behavior:** Fail safe to HOLD/INVESTIGATE.
- **Security Constraint:** Hardcoded business logic, cannot be modified by agent.

## 7. Agent Reasoning Requirements
- **Heterogeneous Document Interpretation:** 
  - *Why:* Evidence inputs might have slightly differing schemas in reality.
  - *Input:* JSON evidence bundle.
  - *Output:* Structured extraction of key fields for the tools.
  - *Verified by:* Schema Validator tool.
- **Constructing Investigation Explanation:**
  - *Why:* The human reviewer needs to understand *why* an anomaly was triggered.
  - *Input:* Output of the Rule Evaluator tool.
  - *Output:* Human-readable `required_human_next_step` and `uncertainty` text.
  - *Verified by:* Must map directly to the deterministic anomalies found.

## 8. Orchestration Requirements
**Workflow Flow:**
OBSERVE (Ingest bundle) → EXTRACT (Agent maps fields) → TOOL VERIFY (Deterministic math and equality) → APPLY RULES (Deterministic mapping to rulebook) → CHECK COMPLETENESS (Ensure all lines checked) → EXPLAIN (Agent writes summary) → HUMAN ESCALATION (Final Output).
- **Allowed Transitions:** Strict forward flow.
- **Required Checkpoints:** Must pass tool verification before applying rules.
- **Retry Conditions:** Extraction failures retry up to 2 times.
- **Invalid-Data Handling:** Immediate escalation (INVESTIGATE) if evidence is malformed.
- **Ambiguous Evidence Handling:** Record uncertainty, escalate to INVESTIGATE.
- **Stop Conditions:** Completion of rule evaluation across all items and documents.

## 9. State/Memory Requirements
- **Working Memory:** Required to store extracted fields before passing to tools. Lifetime: Single run. Source of truth: Evidence bundle. Modifiable by: Agent/Tools.
- **Audit History:** Required to trace what tool was called when. Lifetime: Persistent log. Source of truth: Orchestration trace. Modifiable by: Deterministic orchestration only (append-only).
- **Long-term memory / Vector DBs:** NOT REQUIRED. Single case execution contains all needed context.

## 10. Human-in-the-Loop Boundary
**Trigger:** 
- Any HOLD or INVESTIGATE finding (e.g., Unverified Bank Change, Math Error, Missing PO).
- Tool failure, schema failure, or extraction failure.
- Consequential final action (always).
**Agent Action:** Stop execution, compile evidence trace, formulate `required_human_next_step`.
**Human Decision:** Review evidence, authorize payment manually outside the system, or contact supplier.
**Allowed Continuation:** The agent's job terminates here. The agent must NEVER execute payment.

## 11. Evidence / Tracing Requirements
Every decision must record:
- **Source evidence:** Hashes of the input documents.
- **Extracted values:** The exact data points pulled by the LLM.
- **Tool calls/results:** Exact payloads sent to the Math and Equality tools, and their results.
- **Rule evaluations:** The mapping logic used to flag anomalies.
- **Findings:** The exact rulebook anomaly triggered.
- **Recommendation:** PAY, HOLD, INVESTIGATE.
- **Uncertainty/escalation:** Nuanced human-readable explanation.
- **Timestamp/Run identifier:** Unique ID for the execution trace.

## 12. Metric Mapping
- **Evidence Citation / Attribution Correctness:** Measured by the Audit Log validating that the agent extracted strings exactly as they appear in the source documents. (Hybrid Extraction Component).
- **Finding Completeness:** Measured by the Deterministic Rule Evaluator ensuring no anomaly checks were skipped. (Completeness Component).
- **Deterministic Calculation Correctness:** Measured by the Math Tool successfully trapping errors. (Math Component).
- **Calibrated Escalation & Unsafe-PAY Rate:** Measured by the Final Output against the ground truth. (Final Recommendation Component).

## 13. Baseline Differentiation
What exactly will be different about our system compared with the existing single-pass baseline?
- **Iterative Verification:** Instead of guessing the math, the agent delegates math to a strict Deterministic Calculator.
- **Targeted Tool Usage:** The agent is restricted from making business rule judgments; it only maps data, while a deterministic Rule Evaluator enforces the business logic.
- **Structured Audit Trace:** We gain 100% transparent provenance of exactly *why* a math error was flagged via explicit tool calls, rather than relying on an LLM's inline chain-of-thought.

## 14. Failure Handling
| FAILURE | DETECTION | PREVENTION | RECOVERY | HUMAN ESCALATION |
|---|---|---|---|---|
| Malformed input | Schema Validator on ingest | Strict typing | Fail-fast | INVESTIGATE |
| Calculation failure | Tool throws exception | Strict numeric parsing | Retry extraction | HOLD / INVESTIGATE |
| Semantic mismatch | String Equality checker | Strict matching | Re-verify | INVESTIGATE |
| Hallucinated citation | Audit log mismatch | Evidence grounding | Retry | INVESTIGATE |
| Unsafe PAY attempt | Rule Evaluator override | Deterministic enforcement | Force HOLD | HOLD |

## 15. Security Boundaries
The agent MUST NEVER access or modify:
- Hidden ground truth (`data/cases/ground_truth/`).
- Evaluator implementation scripts.
- Benchmark secrets or test manifests.
- External payment execution interfaces or bank APIs (Air-gapped execution).
- Arbitrary filesystem access (No shell tools).

## 16. Minimum Winning Architecture
A lightweight orchestration script (e.g., Python) that wraps the LLM for data extraction and explanation generation, alongside strict deterministic tools (Calculator, Equality Checker, Rule Evaluator). No complex multi-agent swarms, no vector databases, no web frontends, and no long-term memory required.

## 17. Implementation Readiness
- **MUST BUILD:** Orchestration script, Data Extraction Prompt, Deterministic Calculator Tool, Deterministic Equality Tool, Deterministic Rule Evaluator, Audit Logger.
- **SHOULD BUILD:** Automated retry loop for extraction failures.
- **DO NOT BUILD:** Vector database, frontend UI, autonomous payment executor, multi-agent frameworks, long-term state management.

## 18. Explicit Non-Goals
- Achieving 100% autonomous resolution of exceptions (human is always required for HOLD/INVESTIGATE).
- Processing non-invoice financial documents.
- Integrating with live ERP systems during the hackathon.

## 19. Inputs/Outputs
- **Input:** `public_evidence_bundle.json`
- **Output:** `output_contract.json`

## 20. Phase 3.3 Prerequisites
- Phase 3.2 Gate Review Approval.
- Authorization to begin Agent implementation and tool scaffolding.
