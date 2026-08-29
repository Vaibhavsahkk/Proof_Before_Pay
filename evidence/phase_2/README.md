# Phase 2 Evidence

**STATUS: API-independent scaffold tested, actual baseline run NOT RUN, Phase 2 incomplete. Blocked only on local GEMINI_API_KEY after scaffold verification.**

This directory will contain the evidence output for Phase 2 (Fair Baseline), including:
1. `runs/<run_id>/`: The exact raw outputs and run_manifest from the LLM for each test case.
2. `runs/<run_id>/evaluation_report.json`: The computed accuracy and safety metrics based on `eval/evaluate_baseline.py`.
3. `reproduction.txt`: Instructions to reproduce the baseline from a clean clone.

*Actual model outputs/metrics are currently UNVERIFIED and pending key.*

## Reproduction Command
To reproduce the Phase 2 baseline (requires `GEMINI_API_KEY` to be set in environment):

```bash
python -m baseline.run_baseline
python -m eval.evaluate_baseline evidence/phase_2/runs/<run_id>
```
