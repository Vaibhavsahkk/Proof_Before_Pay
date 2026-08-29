# Phase 1: Benchmark Design

## Overview
This directory contains the core elements of the Phase 1 benchmark for the Pre-Payment Exception Investigator. The benchmark evaluates whether an LLM-based agent can reliably analyze a suite of supplier payment evidence documents and correctly recommend PAY, HOLD, or INVESTIGATE, avoiding potentially fraudulent or inaccurate payouts without causing excessive manual reviews for healthy transactions.

## Rulebook
The ground truth is derived deterministically from the [RULEBOOK.md](./RULEBOOK.md). The rulebook details exactly what constitutes an exception that merits a HOLD (such as a Duplicate Invoice, Quantity Mismatch, or Material Price Contradiction) or INVESTIGATE (e.g., Unverified Bank Change).

## Evaluation
See `eval/EVAL_DESIGN.md` for details on how we measure agent performance. Our primary metric is Exact Case-Level Recommendation Accuracy, ensuring the agent matches the required ground truth. 

## Synthetic Data Guarantee
All data used in this benchmark is completely synthetic. There are 6 cases provided in `data/cases/public/` for the agent, and their true labels are available only to the evaluator in `data/cases/ground_truth/`. The runtime and evaluator use separate Docker build targets so the agent image cannot read the answer key. Leakage between the public bundle and ground truth is strictly guarded against.
