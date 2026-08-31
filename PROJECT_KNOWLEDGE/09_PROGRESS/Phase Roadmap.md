# Phase Roadmap

## Phase 0 - Environment and Governance

Status: APPROVED.

Evidence: governance files, Docker build/smoke/tests, security assertions, clean-clone proof, external approval.

## Phase 1 - Problem Scope and Benchmark Design

Status: APPROVED.

Required output: target user, evidence types, anomaly taxonomy, output contract, safety boundaries, strict schemas, independently verified ground truth, frozen manifest, fair evaluation design, and runtime isolation.

Current evidence: 6 synthetic cases, deterministic oracle, manifest verifier, 29 focused tests, 46-test PowerShell and Git Bash pipelines, clean-clone evidence.

## Phase 2 - Fair Baseline

Status: PHASE FAIL - REMEDIATION ACTIVE.

Observed completed Phase 2 facts: recorded exact provider/model/version, prompt, tools, settings, raw outputs, evaluator outputs, runtime, and cost. Used the frozen Phase 1 cases without changes.

## Phase 3 - Failure Analysis

Status: LOCKED.

Map every proposed agent capability to an observed baseline failure or explicit requirement. Reject decorative complexity.

## Phase 4 - Minimal Agent V1

Status: APPROVED.

Build the smallest useful workflow: ingest -> extract -> reconcile -> deterministic checks -> verify -> reviewer-ready report.

## Phase 5 - Memory, History, and Human Review

Status: ACTIVE.

Add only evidence-backed capabilities such as vendor aliases, prior-transaction context, uncertainty handling, and explicit human checkpoints.

## Phase 6 - Security and Sandbox

Status: LOCKED.

Prove safe mounts, credential isolation, bounded tool calls, resource/time limits, trace sanitization, and absence of payment execution.

## Phase 7 - Final Evaluation

Status: LOCKED.

Run baseline and final agent on the same frozen cases. Report primary metric, Unsafe-PAY rate, attribution, calculation accuracy, failures, and improvement delta.

## Phase 8 - Improvement Changelog and Hot Take

Status: LOCKED.

Document only executed experiments, including removed approaches, observed evidence, and decisions.

## Phase 9 - Submission Engineering

Status: LOCKED.

Prepare complete code, README, reproduction guide, changelog, trajectories, evaluation report, security notes, and a video up to 5 minutes.

## Phase 10 - Final Submission Audit

Status: LOCKED.

Reproduce everything from a clean environment, verify all official deliverables and safety constraints, and obtain final external authorization before submission.
