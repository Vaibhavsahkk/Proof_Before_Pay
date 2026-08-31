# Sub-Phase A1 Report — Track B Design & Dataset Freeze

**Phase:** A (Measurement Foundation) — Sub-phase A1
**Status:** COMPLETE — AWAITING GATEKEEPER APPROVAL
**Date:** 2026-08-31
**Executor HEAD at execution:** `adc33289e6272496d769fc8b26fb43e34b529a1e`
**Execution evidence:** `evidence/phase_track_b/A1_execution_evidence.txt`

---

## 1. Objective (per roadmap)

Design a separate "Messy Real-World Document Evaluation" track (10–15 cases),
define case format, ground-truth format, evaluation methodology, baseline,
final agent, primary metric, secondary metrics — and **freeze the Track B
dataset before scoring, with no modification after results are seen.**

## 2. What was delivered

| Artifact | Purpose |
|---|---|
| `data/track_b/DESIGN.md` | Frozen design document (v1.0). Written and frozen **before** any case was scored. |
| `data/track_b/generate_track_b.py` | Deterministic dataset generator. Renders 12 case bundles as PDF / PNG / JSON documents. |
| `data/track_b/cases/case_101..112/` | Frozen case documents + `bundle.json` (the only system input per case). |
| `data/track_b/ground_truth/case_101..112.json` | Ground truth with canonical bundle, render spec, and **oracle-derived** labels. |
| `data/track_b/MANIFEST.sha256` | SHA-256 manifest over all 73 frozen files. |
| `data/track_b/verify_track_b.py` | Integrity gate (details in §4). |
| `tests/test_track_b_freeze.py` | 14 pytest tests wrapping the freeze guarantees. |
| `evidence/phase_track_b/A1_execution_evidence.txt` | Real-command execution log. |

## 3. Dataset design (frozen summary — full detail in DESIGN.md)

- **12 cases** (`case_101`–`case_112`), all synthetic vendors
  (SYNTHETIC / FAKECORP / MOCK / PSEUDO / TESTAMENT).
- **Documents per case:** rendered supplier invoice (PDF), purchase order
  (PDF/PNG/absent), goods receipt (PDF/PNG/absent), vendor master
  (PDF/JSON/absent), plus remittance advice and bank-change notice PDFs where
  the evidence exists. 61 document files total across 3 formats.
- **"Messy" = format variation, not corruption.** Varying field labels,
  layouts, scan-style watermark/footer noise, embedded evidence documents,
  missing documents, cross-document contradictions, multi-item tables.
  Explicitly *excluded* (declared pre-run in DESIGN.md §3): corrupted digits,
  thousands separators, European decimals, illegible values. Track B tests
  format tolerance and cross-document reconciliation, not OCR archaeology.
- **Label distribution (all derived, none authored):**
  2 PAY / 6 HOLD / 4 INVESTIGATE → 10 non-PAY cases form the Unsafe-PAY
  denominator.
- **Challenging case:** `case_111` — duplicate billing + unverified bank
  change, heavy invoice noise, PO as PNG, vendor master as JSON, remittance +
  bank-notice PDFs. Expected (oracle-derived): HOLD with both findings.

## 4. Ground-truth integrity — the anti-targeting guarantee

**No expected label was hand-authored.** For every case,
`expected_recommendation` and `expected_findings` are the output of the
official `Phase1Oracle` from `scripts/validate_phase1.py` — the same
deterministic rule engine used for the official Track A benchmark — applied to
the case's canonical bundle. Both the verifier and the test suite
**re-derive the labels and fail on any drift**. This means:

- The dataset could not be tuned toward a desired score (Absolute Rule 2).
- The dataset was frozen and hashed **before** either system ran on it
  (manifest SHA-256 recorded in evidence).
- Baseline and agent will be scored against identical frozen documents.

## 5. Verification performed (all real executions)

1. `python data/track_b/generate_track_b.py` — exit 0. **Refuses to run into
   an existing tree** (freeze guard).
2. `python data/track_b/verify_track_b.py` — **exit 0,
   `TRACK B VERIFICATION PASSED`**. Checks: manifest integrity (no missing /
   extra / hash-mismatched files), exact inventory, bundle↔file agreement,
   PDF magic + text-layer parseability, PNG magic, JSON parseability,
   ground truth == official oracle re-derivation, canonical validity against
   the **unmodified official** `public_evidence_bundle.json` schema,
   synthetic-vendor rule, leakage rules on all system inputs, exactly one
   challenging case, and **byte-level generator determinism** (regenerated
   manifest identical to the frozen manifest).
3. `python -m pytest tests/test_track_b_freeze.py -q` — **14 passed**.
4. Mandatory regression (official benchmark untouched):
   - `python scripts/validate_phase1.py` — `ALL PHASE 1 VALIDATIONS PASSED`, exit 0.
   - `python scripts/verify_manifest.py` — `Manifest verification passed.`, exit 0.
   - `python scripts/evaluate_agent.py` — 100% / 100% / 0.0% unsafe-PAY, exit 0.
5. Full suite: `python -m pytest --ignore=tests/test_environment.py -q` —
   **163 passed, 0 failed** (103.51s; `test_environment.py` requires the
   Linux Docker container by design and is covered by the Docker pipelines).

## 6. Defects found and fixed during A1 (honest record)

1. **Verifier path-resolution bug:** ground-truth manifest entries were
   resolved against the wrong root → 12 false "missing file" failures. Fixed
   in `verify_track_b.py` (dataset files untouched).
2. **Over-broad leakage check:** answer-key indicators were initially applied
   to evaluator-side ground truth, which legitimately contains labels
   (exactly like Track A's own `data/cases/ground_truth/`). Leakage rules now
   apply to **system inputs only** (case documents + bundles), matching the
   official Track A policy.
3. **Non-deterministic PDF bytes:** PyMuPDF embeds a random trailer `/ID` file
   identifier per run (sometimes hex, sometimes binary). The generator now
   normalizes it to a constant, and the verifier proves byte-level
   reproducibility by regenerating into a temp root and comparing manifests.
   The frozen dataset was regenerated after this fix and re-verified —
   **no Track B case was scored at any point before the final freeze.**

## 7. Frozen fingerprints

- Track B manifest: `data/track_b/MANIFEST.sha256`
- SHA-256 of the manifest file itself:
  `3711501A354C9F0C40B0C1831E42D06415A26C03E10AFEA54FD9CD4A3F6ABDE2`
- Official Track A benchmark: **unmodified** (verified via
  `scripts/validate_phase1.py` + `scripts/verify_manifest.py`).

## 8. A1 file footprint (files added; nothing existing modified)

```
?? data/track_b/                      (DESIGN.md, generator, cases, ground truth, manifest, verifier)
?? evidence/phase_track_b/A1_execution_evidence.txt
?? tests/test_track_b_freeze.py
```

All pre-existing modified files in the working tree (`src/`, `reports/`,
Obsidian state, etc.) predate A1 and were not touched during this sub-phase.

## 9. Remaining unknowns / declared limitations

1. **PNG rendering legibility for multimodal OCR** (used by PO/GRN PNGs in
   cases 102, 105, 111) is *proven parseable and value-complete at the byte
   level*, but the end-to-end OCR extraction quality is measured in A4, not
   A1. The default bitmap font is used; if A4 shows extraction failures
   caused by font size, the honest remedy is a **v1.1 version bump** with a
   documented changelog entry — never a silent edit after scores are seen.
2. **Baseline prompt text** is envelope-frozen in DESIGN.md §7 but the exact
   literal prompt is implemented and hash-pinned in A2, before any Track B
   case is scored.
3. Track B runs (A3/A4) require a live `GEMINI_API_KEY` for the PNG multimodal
   path; run artifacts will be committed for offline verification (D4).
4. `test_environment.py` runs only inside the Linux container by design; the
   Docker pipelines cover it.

## 10. Next sub-phase (BLOCKED until Gatekeeper approval)

**A2 — Fair Baseline (Track B):** implement the one-prompt baseline per the
envelope frozen in DESIGN.md §7 (same documents, same contract, same
generation settings), freeze and hash its exact prompt, add tests, and STOP.

---

**SUB-PHASE A1 COMPLETE. STOPPED. AWAITING GATEKEEPER REVIEW.**
