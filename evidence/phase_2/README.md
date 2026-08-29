# Phase 2 Evidence

**STATUS: API-independent scaffold verified. Attempts with unavailable 2.5 Pro and zero-quota 3.1 Pro are INVALID; no valid Phase 2 metric exists yet.**

This directory will contain the evidence output for Phase 2 (Fair Baseline), including:
1. `runs/<run_id>/`: The exact raw outputs and run_manifest from the LLM for each test case.
2. `runs/<run_id>/evaluation_report.json`: The computed accuracy and safety metrics based on `eval/evaluate_baseline.py`.
3. `reproduction.txt`: Instructions to reproduce the baseline from a clean clone.

The human supplied `GEMINI_API_KEY` locally without sharing it in chat or evidence. `runs/run_20260829_151625_260ba740/` preserves the failed provider-availability attempt, and `runs/run_20260829_152146_25ba3699/` preserves the failed Pro-quota attempt. Both evaluator reports are INVALID. The retry is pinned to successfully probed `gemini-3.6-flash`.

Scaffold verification logs:

- `scaffold_verify_powershell.txt`
- `scaffold_verify_git_bash.txt`
- `scaffold_clean_clone_execution.txt`

## Reproduction Command
To reproduce the Phase 2 baseline (requires `GEMINI_API_KEY` to be set in environment):

```bash
python -m baseline.run_baseline
python -m eval.evaluate_baseline evidence/phase_2/runs/<run_id>
```
