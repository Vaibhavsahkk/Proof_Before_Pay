# Remediation: Extraction Field-Contract Defect (2026-09-02)

Scope: the dominant agent failure identified by the A5 Track B measurement
(dropped item-level `quantity`/`unit_price` → false `Math Error` HOLDs on
cases 102/109/112) plus the surrounding reproducibility defects found in the
final deep audit. This report records what was changed, why, and the exact
verification evidence. No frozen historical measurement artifacts
(`evidence/phase_track_b/A4_agent_version_freeze.json`, frozen run dirs,
`reports/phase_A5_track_b_measurement.md`) were modified.

## 1. Root cause

`google-genai` `response_schema` does not support the JSON-Schema `required`
keyword. When the item schema was passed to Gemini, the SDK silently stripped
`required` from the wire schema, so the model was free to omit any item field
it chose. With `temperature=0.0` the omissions were stable per case: on
case_102/109/112 Track B documents the model returned items containing only
`item_id` and `line_total`. The deterministic calculator then failed its
3-way check (quantity × unit_price = line_total) and the orchestrator
fail-closed to HOLD with a false `Math Error` finding.

## 2. Fix (src/agent/extraction.py)

1. `ITEM_REQUIRED_FIELDS` — explicit contract listing the required fields per
   document's items (invoice: item_id/description/quantity/unit_price/
   line_total; purchase_order: item_id/quantity/unit_price; goods_receipt:
   item_id/quantity_accepted).
2. `ITEM_CONTRACT_TEXT` — reinforced prompt section: the schema is also
   inlined as text with the contract, because the wire schema alone cannot
   carry `required`.
3. `_missing_item_fields(data)` — post-extraction validator returning
   `(document, field, affected_count)` tuples. Absent documents are not
   violations (a genuinely missing GRN stays missing evidence).
4. One reinforced retry — when the first response violates the contract,
   the exact violation detail is appended and the model re-extracts; the
   better of the two responses (fewer violations) is kept.
5. `_repair_item_arithmetic(data)` — deterministic Decimal completion when
   two of {quantity, unit_price, line_total} are present: derives the third.
   Never fabricates: every derived value is grounded in two extracted values.
6. `_repair_from_purchase_order(data)` — self-verifying cross-document
   completion for invoice items: fills quantity/unit_price from the matching
   PO item ONLY when the invoice's own `line_total` exactly equals
   PO quantity × unit_price (exact Decimal equality). A genuine
   price-mismatch invoice therefore rejects the fill and keeps its
   incomplete item, preserving the calculator's fail-closed error path.
7. `_fill_missing_descriptions(data)` — `description` is schema-required
   but never consumed downstream (verified: zero usages in rule evaluator,
   calculator, equality checker). If still missing after the retry, it is
   filled with an empty string (honest absence) instead of failing the case.

## 3. Verification evidence

- Offline unit checks: contract validator (satisfied/absent/violation shapes),
  arithmetic repair (all three derivations, garbage left untouched), PO
  cross-repair (109-shape fill, deliberate price-mismatch REJECTED, partial
  fills, no-id-match untouched) — all pass.
- Live cache-cleared runs through the production DocumentAdapter flow
  (PDF text + PNG multimodal OCR), forced to the quota-available
  `gemini-2.5-flash` bucket because the `gemini-3.6-flash` free-tier daily
  quota was exhausted at fix time:
  - case_102 → `PAY / []` — exact match with ground truth.
  - case_109 → `INVESTIGATE / [Vendor Identity Mismatch]` — exact match.
  - case_112 → `INVESTIGATE / [Missing GRN, Missing Vendor Master]` plus
    one additional cascade finding `Missing GRN Line ID` (the frozen
    baseline run also emits this finding on case_112; recommendation and
    all expected findings match).
  - Extracted invoice items after fix: `PAPER-A4 40×12.50=500.00`,
    `PEN-BL 20×2.50=50.00`, `GASKET-9 8×75.00=600.00`, `HVAC-SVC
    2×225.00=450.00` — all exact document values, zero contract violations.
- Full suite: 163/165 host (the 2 host failures are container-only
  environment tests: python version and non-root user, both by design —
  they assert the Docker runtime); 165/165 in the Linux verifier container
  with the fixes mounted.

## 4. Reproducibility fixes shipped alongside

- `data/track_b/verify_track_b.py`: the determinism gate compared
  regenerated PNG files byte-for-byte. Root cause of the Linux failure:
  Pillow's bundled zlib encoder differs between the Windows and Linux wheels
  of the same Pillow version; pixel data is byte-identical (MD5 of decoded
  RGB verified equal across platforms on all three differing entries:
  case_102/purchase_order.png, case_105/goods_receipt.png,
  case_111/purchase_order.png). The gate now compares PNG entries via
  decoded pixel hash and everything else byte-exact. Frozen dataset and
  MANIFEST.sha256 are untouched. Passes on Windows host and Linux container.
- `demo_recovery.py`: patched the wrong attribute (`extractor.client` —
  the extractor builds a fresh `genai.Client` per attempt, so there is no
  persistent client). Now patches `genai.Client.models`; uses cache-exempt
  `case_000` so the failover path always exercises the live (mocked) API;
  prints masked keys only (a raw-key print was found and removed). Runs to
  completion, exit 0, offline.
- `tests/test_phase4_1_e2e.py`: the three CLI end-to-end tests now inject an
  offline sentinel `GEMINI_API_KEY` into their subprocess environments.
  `src/main.py` hard-checks the variable's presence before any cache use;
  the runs stay fully offline via cached extractions. This keeps
  `docker-compose.yml` credential-free (the compose security invariant and
  its test are unchanged and pass).
- `REPRODUCE.md`: stale run id `run_20260829_154058_02e9416b` (directory
  does not exist) replaced with the accepted run
  `run_20260830_091031_f1cc354c`.
- `requirements.lock`: the runtime deps imported by
  `src/agent/document_adapter.py` (`pymupdf`, `pypdf`, `pillow`) were
  missing, so fresh clones silently degraded the adapter (guarded imports)
  and test collection crashed on `fitz`. The lock now pins all three
  (pymupdf==1.28.0, pypdf==6.14.2, pillow==12.3.0).
- Hygiene: removed stray `data/cases/ground_truth;C/` (semicolon-named
  directory), unreferenced `test_api.py` (imported undeclared `requests`),
  untracked `.obsidian/workspace.json` (now gitignored), and scratch
  verification files.

## 5. What was deliberately NOT done

- The frozen Track B dataset was NOT regenerated and `MANIFEST.sha256` was
  NOT re-frozen. Regenerating would invalidate the recorded input hashes of
  the frozen baseline/agent runs and the A4 component-freeze record. The
  determinism gate was made platform-correct instead.
- A5 was NOT re-measured post-fix: `gemini-3.6-flash` free-tier daily quota
  (20 requests/day) was exhausted during the fix; the live re-verification
  used the quota-available `gemini-2.5-flash` bucket. Re-running the A5 A/B
  measurement on 3.6-flash is a human decision after quota reset; the
  recorded A5 numbers remain the honest PRE-fix measurement and are labeled
  as such.
- The frozen A4 component hash for `src/agent/extraction.py`
  (`DC33ABEF...`) is a historical record of the measured agent version and
  was intentionally left unchanged; the current file hash is
  `F4BABDB2EAFA5E9E1C30C79520BEF9A13ECCF12302C6EA2917C067D6BB398A00`.
