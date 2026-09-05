# TRACK B — MESSY REAL-WORLD DOCUMENT EVALUATION (v1.0 — FROZEN)

## 0. Freeze Declaration

This document freezes the Track B evaluation design and dataset for the
micro1 Agentic Workflows Hackathon 2026 submission of **Proof Before Pay**.

- Track B dataset version: **v1.0**
- Frozen on: 2026-08-31
- Freeze authority: this file plus `MANIFEST.sha256` (SHA-256 over every case
  document and ground-truth file).
- **After freeze, the dataset may not be modified.** Any change requires a new
  version number (v1.1) and a documented reason in the Improvement Changelog.
  A version bump is never permitted *after* scores are observed on v1.0.

## 1. Purpose

The official benchmark (Track A: `data/cases/public/case_001..012.json`) is
clean, structured JSON. On Track A both the fair baseline and the agent
reached 100% exact recommendation accuracy, so Track A alone cannot show a
measured improvement. Track B measures the same capability under **realistic
document conditions** — the conditions a small-business AP reviewer actually
faces — without touching the frozen official benchmark (Absolute Rule 4).

Track B is a **second, clearly labeled evaluation track**. It does not
replace Track A. Track A results remain valid and reported unchanged.

## 2. What Track B Contains

12 synthetic cases (`case_101` … `case_112`), each a bundle of **rendered
document files** (PDF, PNG image, JSON) representing one supplier payment:

- supplier invoice (PDF)
- purchase order (PDF or PNG)
- goods receipt note (PDF or PNG)
- vendor master record (PDF or JSON)
- prior payment history, when used, embedded in a remittance-advice PDF
- bank-change evidence, when used, embedded in a notification PDF

Case IDs use the `case_101..112` range so they:
- satisfy the official output-contract pattern `^case_\d{3}$` (the agent's
  schema validation and the baseline contract both apply unchanged), and
- can never collide with Track A IDs (`case_001..012`) in the shared
  extraction cache (`data/cache/extractions/`).

All data is synthetic. Vendor names contain the same synthetic markers
enforced on Track A (`SYNTHETIC`, `FAKECORP`, `MOCK`, `PSEUDO`,
`TESTAMENT`). No real invoices, banks, or persons appear.

## 3. Degradation Model (what "messy" means — and what it is NOT)

Permitted, value-preserving degradations (the information a careful human
needs remains recoverable from the documents):

| Degradation | Description |
|---|---|
| Label variation | Field labels differ per case: "Invoice Number:" / "Invoice No.:" / "Inv #" etc. |
| Layout variation | Different field order, grouping, address blocks, tables rendered as text rows |
| Scan-style noise | Watermark lines ("* SCANNED DOCUMENT *"), footer lines ("Page 1 of 1 ..."), scan-reference artifacts |
| Format variation | Same logical document rendered as text PDF, PNG image, or JSON |
| Embedded evidence | Prior payment history inside a remittance advice; bank change inside a notification letter |
| Missing documents | A bundle may genuinely lack the PO, GRN, or vendor master record |
| Cross-document contradictions | PO price vs invoice price, GRN quantity vs invoice quantity |
| Multi-item tables | Several line items per invoice with per-line math |

**Explicitly NOT permitted in v1.0** (declared now, before any run, to keep
ground truth fair and to avoid result targeting in either direction):

- No corrupted digits in amounts, tax IDs, invoice numbers, or item IDs
  (a careful human can always read the canonical value).
- No thousands separators ("2,500.00") or European decimal formats
  ("1.000,50") — amounts are plain decimals ("2500.00").
- No illegible/ambiguous-value cases (fail-closed behavior under illegible
  input is a legitimate future v2 topic, not measured in v1.0).
- No multi-vendor conglomerates, no foreign-language documents.

Rationale: Track B tests **format tolerance, extraction under noise, and
cross-document reconciliation**, not OCR archaeology. This keeps the ground
truth derivable and the comparison fair to both systems.

### Deterministic PNG encoding

The generator renders PNG pixels with Pillow but writes the PNG container with
its own fixed encoder: RGB color type, filter 0 for every scanline, and
DEFLATE stored blocks with fixed zlib framing. This avoids platform-specific
Pillow/zlib compression output while preserving the rendered pixel content.
The frozen v1.0 files remain unchanged; the integrity verifier compares their
decoded pixels with regenerated output for backward-compatible freeze checks.

## 4. Case Inventory (frozen)

| Case | Vendor (synthetic) | Deliberate condition | Documents | Expected rec | Expected findings |
|---|---|---|---|---|---|
| case_101 | SYNTHETIC WIDGETS LLC | none (control, clean) | 4 PDFs | PAY | [] |
| case_102 | FAKECORP STATIONERY INC | none; format variation, 2 items, PO as PNG, vendor as JSON | inv PDF, PO PNG, GRN PDF, VM JSON | PAY | [] |
| case_103 | FAKECORP CONSULTING INC | Duplicate Billing (history in remittance PDF) + watermark | 4 PDFs + remittance | HOLD | [Duplicate Billing] |
| case_104 | PSEUDO PARTS GMBH | Price Contradiction (PO 2.00 vs invoice 2.20) + watermark/footer | 4 PDFs | HOLD | [Price Contradiction] |
| case_105 | MOCK METALS LTD | Quantity Mismatch (GRN as PNG: accepted 45, invoiced 60) | inv PDF, PO PDF, GRN PNG, VM PDF | HOLD | [Quantity Mismatch] |
| case_106 | TESTAMENT FACILITIES LLC | Unverified Bank Change (PENDING notice PDF) | 4 PDFs + notice | INVESTIGATE | [Unverified Bank Change] |
| case_107 | PSEUDO PRINT CO | Math Error (stated line total 600.00; 10 x 50.00) + heavy noise | 4 PDFs | HOLD | [Math Error] |
| case_108 | FAKECORP LOGISTICS INC | Missing PO (no PO document exists) | 3 docs (no PO) | INVESTIGATE | [Missing PO] |
| case_109 | SYNTHETIC WIDGETS | Vendor Identity Mismatch (invoice name lacks "LLC") | 4 PDFs | INVESTIGATE | [Vendor Identity Mismatch] |
| case_110 | MOCK GLOBAL TRADE LTD | Currency Mismatch + Invalid Currency (invoice EUR, PO USD) | 4 PDFs | HOLD | [Currency Mismatch, Invalid Currency] |
| case_111 | TESTAMENT SOFTWARE CORP | **CHALLENGING**: Duplicate Billing + Unverified Bank Change; noisy invoice, PO as PNG, vendor as JSON, remittance + notice PDFs | 6 docs, 3 formats | HOLD | [Duplicate Billing, Unverified Bank Change] |
| case_112 | PSEUDO SERVICES LLC | Missing Vendor Master + Missing GRN (only invoice + PO exist) | 2 PDFs | INVESTIGATE | [Missing GRN, Missing Vendor Master] |

Distribution: 2 PAY / 6 HOLD / 4 INVESTIGATE (10 non-PAY cases form the
Unsafe-PAY denominator). `case_111` is the designated challenging case
required by the official rules.

## 5. Case Format (frozen)

Each case directory `data/track_b/cases/case_1NN/` contains **only**:

- document files with fixed names:
  `invoice.pdf`, `purchase_order.pdf` (or `.png`), `goods_receipt.pdf`
  (or `.png`), `vendor_master.pdf` (or `.json`), `remittance_advice.pdf`,
  `bank_change_notice.pdf`
- `bundle.json`:
  `{"case_id": "case_101", "track": "B", "documents": ["invoice.pdf", ...]}`
  — the ordered stack of documents the reviewer received. It contains no
  answer information.

The systems under evaluation receive **only** the files listed in
`bundle.json`. Ground truth never enters the case directory.

## 6. Ground Truth Format (frozen)

Each `data/track_b/ground_truth/case_1NN.json` contains:

```json
{
  "case_id": "case_101",
  "track": "B",
  "expected_recommendation": "PAY",
  "expected_findings": [],
  "challenging": false,
  "canonical": { ... full public-evidence-bundle object used to render the documents ... },
  "render_spec": { ... exact noise/format profile applied ... },
  "derived_by": "scripts/validate_phase1.Phase1Oracle (official rulebook logic, unmodified)"
}
```

Integrity rules for ground truth:

1. `canonical` **must** validate against the official
   `benchmark/schemas/public_evidence_bundle.json` — unchanged.
2. `expected_recommendation` and `expected_findings` are **derived, never
   hand-authored**: they are the output of the official `Phase1Oracle` from
   `scripts/validate_phase1.py` applied to `canonical`. The verifier
   re-derives them and fails if they drift.
3. The rendered documents are a faithful rendering of `canonical` (all
   canonical values appear in the documents).

Because truth is derived by the same deterministic rule engine used for
Track A, Track B measures the same rulebook — only the input conditions
change.

## 7. Baseline Definition (envelope frozen now; implemented in A2)

Per the official rules, the baseline is *"one direct prompt with basic
instructions"* — the simplest reasonable way a small business would try this
today. To keep the comparison fair, the baseline receives **the same
document files** as the agent:

- **Input:** every document listed in the case's `bundle.json`, attached to a
  single Gemini request in its native format (PDF/PNG as multimodal parts,
  JSON as text) — the baseline is NOT denied any information the agent has.
- **Model/settings:** `gemini-3.6-flash`, temperature 0.0,
  `response_mime_type="application/json"`, max_output_tokens 4096 — the same
  envelope as the accepted Track A baseline.
- **Prompt:** basic instructions to review the attached supplier documents
  and return a PAY / HOLD / INVESTIGATE recommendation with findings, in the
  official output-contract JSON. No rulebook, no tools, no retries beyond
  transient HTTP errors, no second pass — one prompt, one answer.
- **Output:** must satisfy `benchmark/schemas/output_contract.json` with the
  correct `case_id` — the same contract the agent must satisfy.

The baseline is **not** given hidden advantages and **not** intentionally
crippled (Absolute Rule: fair baseline). Its exact prompt text is frozen in
A2 before any Track B case is scored.

## 8. Final Agent Definition (frozen)

The **current, unmodified** pipeline:

`bundle.json documents` → `DocumentAdapter.process_bundle` (native PDF text
extraction via PyMuPDF/pypdf; images via multimodal OCR) →
`AgentOrchestrator.run_workflow` (`LLMExtractor` → deterministic
`DecimalCalculator` / `EqualityChecker` verification → `RuleEvaluator`) →
output contract.

A4 runs this agent exactly as committed. No per-case tuning, no new
capabilities, no changes to fit individual Track B cases.

Known operational dependency (declared now, honestly): PNG documents take
the multimodal OCR path, which requires a live Gemini key at execution time.
Track B is therefore executed in **live mode** with `GEMINI_API_KEY`
supplied through the local environment; committed run artifacts and
extraction caches preserve the results for offline verification afterward
(the offline judge-reproduction command is Phase D4).

## 9. Evaluation Methodology (frozen)

- **Evaluator:** `data/track_b/evaluate_track_b.py` (built in A5; only the
  methodology is frozen here). It is evaluator-only code; ground truth never
  enters the agent or baseline inputs.
- **Same cases, same documents, same contract** for baseline and agent.
- Run artifacts are written immutably under `data/track_b/runs/<run_id>/`
  (exclusive-create files, same discipline as Track A).

### Metrics

**Primary metric — Exact case-level recommendation accuracy (%)**
`correct final recommendation / 12`. User meaning: "does the review reach
the right payment action?" (identical primary metric to Track A and the
frozen eval design).

**Safety metric — Unsafe-PAY rate (%)**
non-PAY cases recommended PAY / 10. For a payment product this is the
catastrophic-error metric.

**Secondary metrics**

| Metric | Definition | Applies to |
|---|---|---|
| Findings exactness % | sorted-set equality of `findings` vs ground truth | both |
| Schema validity % | output satisfies official output contract | both |
| Extraction fidelity % | exact match of extracted values vs `canonical` (invoice_number, vendor_tax_id, currency, total, per-item quantity/unit_price) | agent (baseline does not output structured extractions; reported honestly as unavailable for baseline) |
| Runtime seconds | per-case and total | both |
| Tokens | prompt/candidate counts where the provider returns them | both |
| Cost | USD where computable; else marked UNAVAILABLE | both |

The final comparison uses the official table format:

`METRIC | SIMPLE BASELINE | AGENT SOLUTION | CHANGE`

with every value labeled **measured / estimated / unavailable**. No value is
invented (Absolute Rule 2: no result targeting — the delta is whatever the
runs produce, including a possible delta of zero).

## 10. Integrity & Security Rules (frozen)

1. The official Track A benchmark (`data/cases/`, `benchmark/`,
   `evidence/phase_1/SHA256_MANIFEST.txt`) is **never modified**. The
   verifier for Track B and the existing official manifest verifier both run
   in regression after every Track B sub-phase.
2. No standalone "pay", "hold", or "investigate" tokens and no
   answer-indicator strings in any case document or `bundle.json`
   (same leakage rules as Track A, checked by the verifier).
3. Ground truth lives only under `data/track_b/ground_truth/` and never
   enters case directories or system inputs.
4. No credentials in any Track B file; runs redact keys exactly like
   Track A.
5. Synthetic data only — enforced by the verifier (same keyword rule as
   Track A).
6. Track B is evaluator-side: the Docker `runtime` image does not copy
   `data/track_b/` (its COPY allowlist is unchanged); the `verifier` target
   includes it via the existing `COPY data/ ./data/`.
7. The PDF/PNG renderers use fixed metadata and deterministic layout, so
   the generator reproduces byte-identical artifacts (self-checked).

## 11. Verification Tooling (frozen with v1.0)

- `data/track_b/generate_track_b.py` — deterministic dataset generator +
  oracle-derived ground truth + manifest generation. Regenerating must
  reproduce the exact frozen bytes.
- `data/track_b/verify_track_b.py` — integrity gate:
  manifest match, inventory, bundle/file agreement, document parseability
  (PDF magic + text layer, PNG magic), ground truth == official oracle
  re-derivation, canonical schema validity, synthetic-vendor rule, leakage
  rules, generator determinism.
- `tests/test_track_b_freeze.py` — pytest wrapper. Parts needing PyMuPDF
  are skipped when it is unavailable (e.g., inside the current Docker
  verifier image); manifest, ground-truth, schema, and inventory checks
  run everywhere.

## 12. Runner Contract (defined now; built in A3/A4)

`data/track_b/run_track_b.py --mode baseline|agent [--case case_1NN]`
loads `bundle.json`, feeds the identical documents to the selected system,
records raw outputs/traces/latency/tokens under
`data/track_b/runs/<run_id>/`, and never writes into
`data/track_b/cases/` or `ground_truth/`.

## 13. Non-Goals of v1.0

- No modification of Track A, its evaluator, or its recorded results.
- No new agent capabilities in Phase A (the agent runs as committed).
- No OCR-corrupted values, thousands separators, or illegible documents
  (see Section 3).
- No claims about production performance; Track B is a 12-case synthetic
  benchmark measuring format tolerance and reconciliation under noise.

## 14. Version

**Track B v1.0 — FROZEN 2026-08-31.** Dataset changes after this point are
prohibited until the Track B measurement (A5) is complete and reported.
