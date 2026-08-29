# Phase 2 Fair Baseline

The baseline performs one Gemini call per frozen public case with no tools, memory, or access to hidden ground truth. It is pinned to `gemini-3.6-flash`, the frozen prompt in `prompt_v1.txt`, deterministic generation settings, and the Phase 1 output contract.

Run only from a clean committed source state with `GEMINI_API_KEY` supplied through the process environment. Raw responses and provenance are written immutably under `evidence/phase_2/runs/`; evaluate them offline with `python -m eval.evaluate_baseline <run_dir>`.
