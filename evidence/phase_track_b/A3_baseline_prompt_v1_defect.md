# Track B Baseline Prompt Defect Report — v1 → v2 (pre-scoring)

**Date:** 2026-08-31 (after A3 execution attempt 1, BEFORE any A5 scoring)
**Detected in:** `data/track_b/evaluation/baseline_runs/run_20260831_212344_ef2cfd1a/` (prompt v1)

## Defect

The A2 baseline prompt v1
(`data/track_b/evaluation/baseline_prompt_v1.txt`,
SHA-256 `3CA82D5AD74C1608DBA8663B34873BC8029C0F42191F37C2BFE22A4397B7EA36`)
paraphrased the output-contract keys but did NOT include the official output
contract schema (nor its findings enum). On every case where the model
identifies issues, it therefore emits free-text findings such as
`"Unit price mismatch for item BRK-PAD: Invoice specifies 2.20 USD per unit..."`
instead of the enumerated finding `Price Contradiction`, and the output fails
`benchmark/schemas/output_contract.json` validation.

## Evidence (run 1, prompt v1, all 12 cases, no scoring performed)

| case | status | note |
|---|---|---|
| case_101 | API_ERROR | 503 high-demand (transient, recorded per A3.3) |
| case_102 | SUCCESS | findings empty → trivially valid |
| case_103 | SUCCESS | (missed duplicate billing — capability result, not defect) |
| case_104 | SCHEMA_INVALID | free-text findings not in enum |
| case_105 | SCHEMA_INVALID | free-text findings not in enum |
| case_106 | SCHEMA_INVALID | free-text findings not in enum |
| case_107 | SCHEMA_INVALID | free-text findings not in enum |
| case_108 | SCHEMA_INVALID | free-text findings not in enum |
| case_109 | SUCCESS | (missed vendor identity mismatch — capability result) |
| case_110 | SCHEMA_INVALID | free-text findings not in enum |
| case_111 | SCHEMA_INVALID | free-text findings not in enum |
| case_112 | SCHEMA_INVALID | free-text findings not in enum |

8/12 cases failed the output contract purely because the model was never told
the contract. The smoke case (case_101) did not reveal this because it has no
findings (empty list is trivially valid).

## Why this is a defect against the frozen A1 design

`data/track_b/DESIGN.md` §7 (frozen): the baseline "**Output:** must satisfy
`benchmark/schemas/output_contract.json` with the correct `case_id` — the same
contract the agent must satisfy." The v1 prompt could not satisfy the frozen
requirement on any findings case. Phase instructions (A2.3) explicitly permit
"permitted schema/rule context" as baseline input.

## Remedy (v2)

- v1 is NOT altered; its file and hash remain frozen as defect evidence.
- New versioned artifact: `baseline_prompt_v2.txt` + `baseline_prompt_v2.sha256`.
- v2 = v1 text + the official output-contract JSON embedded inline. The
  rulebook remains EXCLUDED (A1 frozen design: "No rulebook, no tools, no
  retries beyond transient HTTP errors, no second pass").
- The baseline runner accepts the prompt version explicitly; v2 runs are
  recorded under new run IDs; run-1 artifacts are preserved unchanged.
- v2 was created BEFORE any Track B scoring (A5 not executed at the time of
  this fix). No ground-truth or case data was modified. Frozen dataset
  integrity re-verified after the fix.

## What was NOT changed

- No Track B case, ground truth, manifest, design, or verifier file.
- No agent code (A4 runs the committed agent unmodified).
- No scoring: A5 evaluator had not been run on any baseline output when v2
  was created.
