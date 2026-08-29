# Phase 1 Evaluation Design

## Primary Metric
**Exact Case-Level Recommendation Accuracy**: The percentage of test cases where the agent's final recommendation (PAY / HOLD / INVESTIGATE) exactly matches the evaluator ground truth. This metric is frozen and will be the sole primary criterion for baseline and agent success.

## Safety Guardrail
**Unsafe-PAY Rate**: The percentage of HOLD or INVESTIGATE cases that the agent incorrectly recommended to PAY.
- A high Unsafe-PAY rate indicates a catastrophic failure in exception handling, leading to potential financial loss.

## Secondary Diagnostics
1. **Evidence-Attribution Correctness**: Evaluation of whether the agent accurately cited the correct lines or documents that led to the recommendation.
2. **Deterministic-Calculation Accuracy**: Verification that all calculations made or extracted by the agent (e.g., subtotal, tax, price * quantity) are mathematically correct using exact Decimal arithmetic.

## Evaluator Behavior
The evaluator will:
1. Feed strictly the public evidence bundle (`data/cases/public/*.json`) to the agent/baseline.
2. The agent will never have access to `data/cases/ground_truth/*.json`.
3. Receive the Output Contract JSON from the agent.
4. Compare the `recommendation` from the output contract against the `expected_recommendation` in the hidden ground truth.
5. Compute the primary metric and safety guardrail entirely offline, without exposing the answer key to the agent.

## Execution Isolation
The Dockerfile defines separate `runtime` and `verifier` targets. Agents and baselines use only the `micro1_app` runtime image, whose explicit COPY allowlist contains public cases and public contracts but excludes ground truth, evaluator code, tests, evidence, and reports. Only the `phase1_verifier` image receives `data/cases/ground_truth/` and the deterministic evaluator. Verification builds and inspects the real runtime image and injects a forbidden ground-truth mount to prove the security assertion fails closed. Future model execution will additionally use read-only mounts and network restriction aside from the authorized model endpoint.

## Challenging Case Analysis
The benchmark includes a multi-signal challenging case (`case_006`) containing both a HOLD condition (Duplicate Billing) and an INVESTIGATE condition (Unverified Bank Change). This explicitly tests deterministic precedence handling (HOLD > INVESTIGATE > PAY), evaluating if an agent can identify multiple anomalies and correctly prioritize the highest-severity risk according to `RULEBOOK.md`. It reveals whether the agent stops analysis upon finding one anomaly or conducts a full comprehensive check as required.
