# Phase 2 Fair Baseline

The baseline performs Gemini calls per frozen public case with no tools, memory, or access to hidden ground truth (6/6 final successful case outcomes; 9 total provider attempts; 3 transient retries; exact retry status codes/messages UNRECORDED; final successful raw responses preserved). It is pinned to `gemini-3.6-flash`, the frozen prompt in `prompt_v1.txt`, deterministic generation settings, and the Phase 1 output contract.

Run only from a clean committed source state with `GEMINI_API_KEY` supplied through the process environment. Raw responses and provenance are written immutably under `evidence/phase_2/runs/`; evaluate them offline with `python -m eval.evaluate_baseline <run_dir>`.
