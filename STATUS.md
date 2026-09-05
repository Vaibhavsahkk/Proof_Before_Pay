# Project Status

Current phase: Phase A (Track B Measurement) — A4 + A5 COMPLETE
Phase status: MEASURED. The full Track B comparison is recorded in
`reports/phase_A5_track_b_measurement.md` (machine-readable:
`reports/track_b_final_results.json`). Honest headline: the current agent
did NOT beat the fair baseline on primary accuracy (75.00% vs 83.33%,
delta -8.33 pp), while eliminating the unsafe-PAY error (0/10 vs 1/10) and
being the only system to solve the challenging case_111. Dominant agent
failure mode: one extraction defect (dropped quantity/unit_price → false
Math Error, fail-closed direction). Smallest evidence-backed next step
(section 18 of the A5 report) is NOT yet executed and NOT claimed.
Last completed: extraction-contract fix (2026-09-02, see
`reports/remediation_extraction_contract.md`): Gemini `response_schema`
drops the `required` keyword (SDK-unsupported), so item-level
quantity/unit_price were silently omitted on some cases (102/109/112),
producing false Math Error HOLDs. Fix: prompt-reinforced item contract +
post-extraction validation (`_missing_item_fields`) + one reinforced
retry + deterministic Decimal repair (`_repair_item_arithmetic`) +
self-verifying cross-PO completion with exact line_total check
(`_repair_from_purchase_order`) + honest empty-description fallback.
Live re-verification (cache-cleared, production DocumentAdapter flow):
case_102 → PAY/[] exact match; case_109 → INVESTIGATE/[Vendor Identity
Mismatch] exact match; case_112 → INVESTIGATE with both expected findings
(plus one cascade finding "Missing GRN Line ID" that the baseline also
produces on this case; recommendation and all expected findings match).
Docker Desktop daemon was repaired on this host (server 29.6.2); the
Linux container suite now passes 165/165 and the Track B verifier passes
on both Windows and Linux (PNG determinism compared via decoded pixel
data: Pillow's bundled zlib encoder differs per platform wheel while
pixel content is identical — see `verify_track_b.py`).
Known remaining honest gaps: the A5 headline metrics (75.00% vs 83.33%)
are the measurement of the PRE-fix agent version and are NOT re-measured
post-fix (daily free-tier quota for `gemini-3.6-flash` was exhausted at
fix time and remains exhausted as of the latest probe; live re-measurement
is a human decision). The re-measurement runner is ready:
`python data/track_b/evaluation/remeasure_a5.py` pre-checks the quota on
the A4-recorded extraction model (exit 3 with the provider's reset
message when exhausted), clears the 12 Track B caches, then runs and
scores fresh baseline+agent comparisons into NEW result files only. The
extraction fix has since been extended to invoice-level totals
(subtotal/tax/total contract + deterministic repair — see
`reports/remediation_extraction_contract.md` "Post-audit follow-up
fix"), after a live run showed the model dropping invoice totals while
items were perfect; case_112 was re-verified INVESTIGATE with all
expected findings through the repair pipeline.

Production-hardening round (2026-09-06, all live-verified):
1. OCR model resilience — the image/scanned-PDF transcription path
   hardcoded `gemini-2.5-flash`, which returns 404 model-not-found on 4 of
   5 pool keys. The adapter now tries a configurable candidate chain
   (`GEMINI_OCR_MODEL`, then `gemini-3.6-flash`) and treats quota errors
   as per-MODEL buckets: a 429 on the primary falls through to the
   fallback on the same key, and only a rate-limited-everywhere condition
   rotates the key (RetrySignal). Live proof: case_102's PNG purchase
   order now OCRs correctly while 2.5-flash is 404/429, and the full
   production flow returns the exact ground-truth PAY/[].
2. Absent-document guard — the extraction contract previously could not
   distinguish "model dropped the entire purchase_order object" from
   "genuinely no PO in the case" (demonstrated as a false-INVESTIGATE on
   case_102). `_missing_extracted_documents` now flags documents whose
   strong source markers (titles/labels) appear in the evidence text but
   whose objects are missing from the extraction, feeding the same
   reinforced retry. Genuinely-absent documents never trigger it
   (case_112 shape re-verified: no false Missing-PO flags).
3. Credential-cooldown test determinism — `test_orchestrator_resume_state`
   was racy: with a real clock, the orchestrator's ~60 s cooldown wait
   could land just before/after key A's recovery and flip the rotated-key
   assertion. The test now freezes `src.agent.credentials.time.time` and
   no-ops the orchestrator sleep (15/15 stable consecutive runs).
4. Reviewer-UI hardening — `/api/investigate` now requires an
   `X-Auth-Token` (constant-time compare; 401 without/with-wrong token,
   live-verified), the token is auto-injected into the same-origin UI
   page (strict CORS default `null` — no cross-origin browser access),
   request bodies are capped (`PBP_UI_MAX_BODY_BYTES`, default 20 MiB,
   413 live-verified), and all test servers use OS-assigned ephemeral
   ports to eliminate cross-run socket interference.
   `tests/test_production_hardening.py` carries 17 regression tests for
   all of the above; host suite is 181 passed / 2 container-only skipped,
   and the full `verify.sh` Docker pipeline (build, container suite,
   Phase 1 validator, manifest, smoke, security assertions, forced-
   failure isolation) passes end-to-end on this tree.

Human actions required: review the A5 report and the post-fix live
re-verification above; decide whether to re-measure A5 with the fixed
agent once `gemini-3.6-flash` daily quota resets (recommended before
submission), then push.

## Accepted Phase 2 baseline

- Run: `evidence/phase_2/runs/run_20260830_091031_f1cc354c`.
- Source commit: `2f7602a33dcbed5c36886e8e7e2d116e66291708`; source tree recorded clean.
- Provider/model: Google Gemini, requested and returned `gemini-3.6-flash`.
- SDK: `google-genai==2.20.0`.
- Manifest: `phase2-baseline-run-v2`; input hashes use `utf8-text-normalized-lf`.
- 12/12 final successful case outcomes; final successful raw responses preserved.
- Evaluator status: VALID.
- Exact case-level recommendation accuracy: 100.0%.
- Findings correctness: 100.0%.
- Schema validity: 100.0%.
- Unsafe-PAY rate: 0/10, 0.0%.
- Runtime: 121.17994389999967 seconds total; 10.098328658333307 seconds mean.
- Tokens: 23,314 prompt and 3,095 candidate.
- Cost: UNKNOWN; no unsupported price estimate is claimed.

## Verification summary

- Independent read-only run audit: PASS for all canonical input hashes, output hashes, rendered-prompt hashes, schemas, case bindings, raw-response equality, metadata, calculations, citations, metrics, and common secret patterns.
- Existing-report deterministic re-evaluation: PASS, exit 0.
- Focused Phase 2 suite: PASS, 35 tests.
- Full PowerShell Docker pipeline: PASS, 81 tests, exit 0.
- Full Git Bash Docker pipeline: PASS, 81 tests, exit 0.
- Exact remote clean-clone gate: PASS on `1ffb2281ff79e69d84439ab9c9ad87e853cf6e2c`.
- Clean-clone committed-report verification: PASS.
- Missing-key rejection: PASS with exact expected message and exit 1.
- Post-test clone Git status: empty.
- Exact temporary clone and Compose resources: removed.
- Final normalized clean-clone log SHA-256: `D720522023C2ACBB17399E1F47A976FD2894FBBD1E4E3AD761518E5E159D2D15`.

## Superseded attempts

- `run_20260829_151625_260ba740`: INVALID, six HTTP 404 responses from unavailable `gemini-2.5-pro`.
- `run_20260829_152146_25ba3699`: INVALID, six HTTP 429 responses because Pro free-tier quota was zero.
- `run_20260829_152514_caab4d45`: evaluator-local result was VALID, but clean-clone verification exposed CRLF-dependent v1 input hashes. It is superseded and its metrics are not decision evidence.

## Assumptions and risks

- Native macOS/Linux execution is unverified; the verified POSIX-like pipeline uses Git Bash on Windows.
- No vulnerability/CVE scanner was run, and no remediation claim is made.
- Cost remains UNKNOWN.
- The twelve-case synthetic benchmark is intentionally small; benchmark reports state performance on that set only and make no production-generalization claim. Track B (12 further rendered-document cases) likewise supports no production-generalization claim.

## Evidence

- `evidence/phase_2/runs/run_20260830_091031_f1cc354c/`
- `evidence/phase_2/final_clean_clone_execution.txt`
- `reports/phase_2_review_packet.md`
- `reports/phase_4_3_final_reproducibility_audit.md`
- `reports/phase_4_4_reviewer_simulation.md`
