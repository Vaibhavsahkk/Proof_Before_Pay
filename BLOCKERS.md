# BLOCKERS

## Phase 2 real baseline credential

- Evidence: `GEMINI_API_KEY` is absent; the clean-clone scaffold gate intentionally observed the exact missing-key rejection in `evidence/phase_2/scaffold_clean_clone_execution.txt`.
- Impact: the real six-case Gemini baseline cannot run, so Phase 2 metrics remain unverified.
- Smallest human action: set `GEMINI_API_KEY` locally without pasting it into chat, source files, logs, or evidence, then report only `Gemini key ready`.

No other blocker is known.
