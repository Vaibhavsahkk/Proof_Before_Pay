# Phase 2 Evidence

**STATUS: API-independent scaffold verified. Baseline attempt 1 is INVALID because the provider rejected unavailable `gemini-2.5-pro`; no valid Phase 2 metric exists yet.**

This directory will contain the evidence output for Phase 2 (Fair Baseline), including:
1. `runs/<run_id>/`: The exact raw outputs and run_manifest from the LLM for each test case.
2. `runs/<run_id>/evaluation_report.json`: The computed accuracy and safety metrics based on `eval/evaluate_baseline.py`.
3. `reproduction.txt`: Instructions to reproduce the baseline from a clean clone.

The human supplied `GEMINI_API_KEY` locally without sharing it in chat or evidence. `runs/run_20260829_151625_260ba740/` preserves the failed provider-availability attempt and its INVALID evaluator report. The retry is pinned to `gemini-3.1-pro-preview`.

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
