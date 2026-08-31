"""Track B dataset generator — v1.0 (FROZEN).

Generates the 12-case Messy Real-World Document Evaluation dataset:
  data/track_b/cases/case_1NN/          document files + bundle.json
  data/track_b/ground_truth/case_1NN.json
  data/track_b/MANIFEST.sha256

Design contract: data/track_b/DESIGN.md (frozen before generation).

Ground truth is DERIVED, never hand-authored: expected_recommendation and
expected_findings are the output of the official Phase1Oracle
(scripts/validate_phase1.py) applied to each case's canonical bundle —
the same deterministic rule engine used for the official Track A benchmark.

Deterministic: fixed metadata, fixed layouts, fixed PNG seeds. Running this
script twice must reproduce byte-identical artifacts (self-checked by
scripts via regenerate-into-temp + manifest equality in verify_track_b.py).
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.validate_phase1 import Phase1Oracle  # noqa: E402  official oracle, unmodified

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None

TRACK_B_DIR = Path(__file__).resolve().parent
CASES_DIR = TRACK_B_DIR / "cases"
GROUND_TRUTH_DIR = TRACK_B_DIR / "ground_truth"
MANIFEST_PATH = TRACK_B_DIR / "MANIFEST.sha256"

PUBLIC_SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "public_evidence_bundle.json"

VERSION = "track-b-v1.0"

# Label dictionaries for format variation (Section 3 of DESIGN.md).
INVOICE_NO_LABELS = ["Invoice Number", "Invoice No.", "Inv #", "Invoice Ref"]
VENDOR_LABELS = ["Vendor", "Supplier", "Vendor Name", "Billed From"]
TAXID_LABELS = ["Tax ID", "VAT ID", "Tax Reg No.", "TIN"]
BANK_LABELS = ["Bank Account", "Remit To Account", "Bank Acc No.", "Payment Account"]


# ---------------------------------------------------------------------------
# Canonical case definitions (values only — all findings are oracle-derived)
# ---------------------------------------------------------------------------

def _item(item_id, description, quantity, unit_price, line_total):
    return {
        "item_id": item_id,
        "description": description,
        "quantity": str(quantity),
        "unit_price": unit_price,
        "line_total": line_total,
    }


def _inv(invoice_number, vendor_name, tax_id, bank, currency, tax_rate, items, subtotal, tax, total):
    return {
        "invoice_number": invoice_number,
        "vendor_name": vendor_name,
        "vendor_tax_id": tax_id,
        "bank_account": bank,
        "currency": currency,
        "tax_rate_percent": tax_rate,
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
    }


def _po(po_number, currency, tax_rate, items):
    return {"po_number": po_number, "currency": currency, "tax_rate_percent": tax_rate,
            "items": [{"item_id": i["item_id"], "quantity": i["quantity"], "unit_price": i["unit_price"]}
                      for i in items]}


def _grn(grn_number, items, accepted=None):
    return {"grn_number": grn_number,
            "items": [{"item_id": i["item_id"],
                       "quantity_accepted": (accepted if isinstance(accepted, str)
                                             else i["quantity"])}
                      for i in items]}


def _vm(name, tax_id, bank):
    return {"vendor_name": name, "vendor_tax_id": tax_id, "bank_account": bank}


def _hist(invoice_number, tax_id, amount, date):
    return {"invoice_number": invoice_number, "vendor_tax_id": tax_id,
            "amount": amount, "payment_date": date}


def _bank_ev(old, new, status, verifier):
    return {"old_bank_account": old, "new_bank_account": new,
            "approval_status": status, "verified_by": verifier}


def canonical_cases():
    """Return the 12 frozen canonical bundles. No expected labels here —
    the oracle derives them (Absolute Rule: no result targeting)."""
    c = {}

    # case_101 — control: clean PAY, text PDFs
    items = [_item("WIDGET-A", "Standard Widget", 100, "5.50", "550.00")]
    c["case_101"] = {
        "invoice": _inv("INV-2101", "SYNTHETIC WIDGETS LLC", "TX-9101", "ACC-1011", "USD", "10.00",
                        items, "550.00", "55.00", "605.00"),
        "purchase_order": _po("PO-3101", "USD", "10.00", items),
        "goods_receipt": _grn("GRN-4101", items),
        "vendor_master": _vm("SYNTHETIC WIDGETS LLC", "TX-9101", "ACC-1011"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_102 — format variation: 2 items, PO as PNG, vendor as JSON -> PAY
    items = [
        _item("PAPER-A4", "A4 Copy Paper Ream", 40, "12.50", "500.00"),
        _item("PEN-BL", "Blue Ballpoint Box", 20, "2.50", "50.00"),
    ]
    c["case_102"] = {
        "invoice": _inv("INV-2102", "FAKECORP STATIONERY INC", "TX-9102", "ACC-1022", "USD", "0.00",
                        items, "550.00", "0.00", "550.00"),
        "purchase_order": _po("PO-3102", "USD", "0.00", items),
        "goods_receipt": _grn("GRN-4102", items),
        "vendor_master": _vm("FAKECORP STATIONERY INC", "TX-9102", "ACC-1022"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_103 — duplicate billing, history inside remittance advice PDF -> HOLD
    items = [_item("SRV-AUD", "Quarterly Audit Support", 1, "800.00", "800.00")]
    c["case_103"] = {
        "invoice": _inv("INV-2103", "FAKECORP CONSULTING INC", "TX-9103", "ACC-1033", "USD", "0.00",
                        items, "800.00", "0.00", "800.00"),
        "purchase_order": _po("PO-3103", "USD", "0.00", items),
        "goods_receipt": _grn("GRN-4103", items),
        "vendor_master": _vm("FAKECORP CONSULTING INC", "TX-9103", "ACC-1033"),
        "prior_payment_history": [_hist("INV-2103", "TX-9103", "800.00", "2026-05-12")],
        "bank_change_evidence": None,
    }

    # case_104 — price contradiction (PO 2.00 vs invoice 2.20) -> HOLD
    inv_items = [_item("BRK-PAD", "Brake Pad Set", 500, "2.20", "1100.00")]
    po_items = [_item("BRK-PAD", "Brake Pad Set", 500, "2.00", "1100.00")]
    c["case_104"] = {
        "invoice": _inv("INV-2104", "PSEUDO PARTS GMBH", "TX-9104", "ACC-1044", "USD", "0.00",
                        inv_items, "1100.00", "0.00", "1100.00"),
        "purchase_order": _po("PO-3104", "USD", "0.00", po_items),
        "goods_receipt": _grn("GRN-4104", inv_items),
        "vendor_master": _vm("PSEUDO PARTS GMBH", "TX-9104", "ACC-1044"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_105 — quantity mismatch (GRN PNG accepted 45 vs invoiced 60) -> HOLD
    inv_items = [_item("STEEL-ROD", "Steel Rod 6mm", 60, "10.00", "600.00")]
    c["case_105"] = {
        "invoice": _inv("INV-2105", "MOCK METALS LTD", "TX-9105", "ACC-1055", "USD", "0.00",
                        inv_items, "600.00", "0.00", "600.00"),
        "purchase_order": _po("PO-3105", "USD", "0.00", inv_items),
        "goods_receipt": _grn("GRN-4105", inv_items, accepted="45"),
        "vendor_master": _vm("MOCK METALS LTD", "TX-9105", "ACC-1055"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_106 — unverified bank change (PENDING notice) -> INVESTIGATE
    items = [_item("FLOOR-CLEAN", "Floor Cleaning Service", 1, "350.00", "350.00")]
    c["case_106"] = {
        "invoice": _inv("INV-2106", "TESTAMENT FACILITIES LLC", "TX-9106", "ACC-9066", "USD", "0.00",
                        items, "350.00", "0.00", "350.00"),
        "purchase_order": _po("PO-3106", "USD", "0.00", items),
        "goods_receipt": _grn("GRN-4106", items),
        "vendor_master": _vm("TESTAMENT FACILITIES LLC", "TX-9106", "ACC-1066"),
        "prior_payment_history": [],
        "bank_change_evidence": _bank_ev("ACC-1066", "ACC-9066", "PENDING", "System"),
    }

    # case_107 — math error (10 x 50.00 but stated 600.00) -> HOLD
    inv_items = [_item("BROCHURE", "Brochure Printing", 10, "50.00", "600.00")]
    c["case_107"] = {
        "invoice": _inv("INV-2107", "PSEUDO PRINT CO", "TX-9107", "ACC-1077", "USD", "0.00",
                        inv_items, "600.00", "0.00", "600.00"),
        "purchase_order": _po("PO-3107", "USD", "0.00", inv_items),
        "goods_receipt": _grn("GRN-4107", inv_items),
        "vendor_master": _vm("PSEUDO PRINT CO", "TX-9107", "ACC-1077"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_108 — missing PO document -> INVESTIGATE
    items = [_item("FREIGHT-LCL", "LCL Freight Charge", 3, "420.00", "1260.00")]
    c["case_108"] = {
        "invoice": _inv("INV-2108", "FAKECORP LOGISTICS INC", "TX-9108", "ACC-1088", "USD", "0.00",
                        items, "1260.00", "0.00", "1260.00"),
        "purchase_order": None,
        "goods_receipt": _grn("GRN-4108", items),
        "vendor_master": _vm("FAKECORP LOGISTICS INC", "TX-9108", "ACC-1088"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_109 — vendor identity mismatch (invoice lacks "LLC") -> INVESTIGATE
    items = [_item("GASKET-9", "Engine Gasket", 8, "75.00", "600.00")]
    c["case_109"] = {
        "invoice": _inv("INV-2109", "SYNTHETIC WIDGETS", "TX-9109", "ACC-1099", "USD", "0.00",
                        items, "600.00", "0.00", "600.00"),
        "purchase_order": _po("PO-3109", "USD", "0.00", items),
        "goods_receipt": _grn("GRN-4109", items),
        "vendor_master": _vm("SYNTHETIC WIDGETS LLC", "TX-9109", "ACC-1099"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_110 — currency mismatch + invalid currency (EUR invoice) -> HOLD
    inv_items = [_item("LAMP-LED", "LED Panel Lamp", 25, "40.00", "1000.00")]
    c["case_110"] = {
        "invoice": _inv("INV-2110", "MOCK GLOBAL TRADE LTD", "TX-9110", "ACC-1100", "EUR", "0.00",
                        inv_items, "1000.00", "0.00", "1000.00"),
        "purchase_order": _po("PO-3110", "USD", "0.00", inv_items),
        "goods_receipt": _grn("GRN-4110", inv_items),
        "vendor_master": _vm("MOCK GLOBAL TRADE LTD", "TX-9110", "ACC-1100"),
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    # case_111 — CHALLENGING: duplicate billing + unverified bank change,
    # noisy invoice, PO as PNG, vendor as JSON, remittance + notice PDFs
    inv_items = [_item("CRM-LIC", "CRM Annual License", 2, "2500.00", "5000.00")]
    c["case_111"] = {
        "invoice": _inv("INV-2111", "TESTAMENT SOFTWARE CORP", "TX-9111", "ACC-9111", "USD", "0.00",
                        inv_items, "5000.00", "0.00", "5000.00"),
        "purchase_order": _po("PO-3111", "USD", "0.00", inv_items),
        "goods_receipt": _grn("GRN-4111", inv_items),
        "vendor_master": _vm("TESTAMENT SOFTWARE CORP", "TX-9111", "ACC-1111"),
        "prior_payment_history": [_hist("INV-2111", "TX-9111", "5000.00", "2026-06-20")],
        "bank_change_evidence": _bank_ev("ACC-1111", "ACC-9111", "PENDING", "System"),
    }

    # case_112 — missing vendor master + missing GRN (only invoice + PO) -> INVESTIGATE
    items = [_item("HVAC-SVC", "HVAC Maintenance Visit", 2, "225.00", "450.00")]
    c["case_112"] = {
        "invoice": _inv("INV-2112", "PSEUDO SERVICES LLC", "TX-9112", "ACC-1122", "USD", "0.00",
                        items, "450.00", "0.00", "450.00"),
        "purchase_order": _po("PO-3112", "USD", "0.00", items),
        "goods_receipt": None,
        "vendor_master": None,
        "prior_payment_history": [],
        "bank_change_evidence": None,
    }

    for case_id, bundle in c.items():
        bundle["case_id"] = case_id
    return c


# Rendering specs per case (fixed so render behavior is part of the freeze):
#   po_format / grn_format / vm_format : "pdf" | "png" | "json"
#   invoice_noise / po_noise           : int 0..3 (0 none, 1 watermark, 2 footer, 3 both)
#   label_set                          : int index into label dictionaries
#   history_doc / bank_doc             : render remittance advice / bank notice when evidence exists
RENDER_SPECS = {
    "case_101": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=0, po_noise=0, label_set=0),
    "case_102": dict(po_format="png", grn_format="pdf", vm_format="json", invoice_noise=0, po_noise=0, label_set=1),
    "case_103": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=1, po_noise=0, label_set=2, history_doc=True),
    "case_104": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=3, po_noise=2, label_set=3),
    "case_105": dict(po_format="pdf", grn_format="png", vm_format="pdf", invoice_noise=1, po_noise=0, label_set=1),
    "case_106": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=0, po_noise=0, label_set=0, bank_doc=True),
    "case_107": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=3, po_noise=1, label_set=2),
    "case_108": dict(po_format=None, grn_format="pdf", vm_format="pdf", invoice_noise=1, po_noise=0, label_set=0),
    "case_109": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=0, po_noise=1, label_set=3),
    "case_110": dict(po_format="pdf", grn_format="pdf", vm_format="pdf", invoice_noise=2, po_noise=2, label_set=1),
    "case_111": dict(po_format="png", grn_format="pdf", vm_format="json", invoice_noise=3, po_noise=1, label_set=0, history_doc=True, bank_doc=True),
    "case_112": dict(po_format="pdf", grn_format=None, vm_format=None, invoice_noise=2, po_noise=0, label_set=2),
}


# ---------------------------------------------------------------------------
# Document rendering
# ---------------------------------------------------------------------------

def _lines_invoice(inv, spec):
    i = spec["label_set"]
    ln, vl, tl, bl = (INVOICE_NO_LABELS[i], VENDOR_LABELS[i], TAXID_LABELS[i], BANK_LABELS[i])
    lines = [
        "SYNTHETIC SAMPLE INVOICE",
        f"{ln}: {inv['invoice_number']}",
        f"{vl}: {inv['vendor_name']}",
        f"{tl}: {inv['vendor_tax_id']}",
        f"{bl}: {inv['bank_account']}",
        f"Currency: {inv['currency']}",
        f"Tax Rate Percent: {inv['tax_rate_percent']}",
        "",
        "Line Items:",
    ]
    for it in inv["items"]:
        lines.append(
            f"Item {it['item_id']} | {it['description']} | Quantity {it['quantity']} | "
            f"Unit Price {it['unit_price']} {inv['currency']} | Line Total {it['line_total']} {inv['currency']}"
        )
    lines += [
        "",
        f"Subtotal: {inv['subtotal']} {inv['currency']}",
        f"Tax Amount: {inv['tax']} {inv['currency']}",
        f"Total Amount: {inv['total']} {inv['currency']}",
    ]
    _apply_noise(lines, spec["invoice_noise"], "INVOICE")
    return lines


def _lines_po(po, spec):
    i = spec["label_set"]
    lines = [
        "SYNTHETIC SAMPLE PURCHASE ORDER",
        f"PO Number: {po['po_number']}",
        f"Currency: {po['currency']}",
        f"Tax Rate Percent: {po['tax_rate_percent']}",
        "",
        "Order Lines:",
    ]
    for it in po["items"]:
        lines.append(
            f"Item {it['item_id']} | Quantity {it['quantity']} | "
            f"Unit Price {it['unit_price']} {po['currency']}"
        )
    _apply_noise(lines, spec["po_noise"], "PO")
    return lines


def _lines_grn(grn):
    lines = [
        "SYNTHETIC SAMPLE GOODS RECEIPT NOTE",
        f"GRN Number: {grn['grn_number']}",
        "",
        "Received Items:",
    ]
    for it in grn["items"]:
        lines.append(f"Item {it['item_id']} | Quantity Accepted {it['quantity_accepted']}")
    return lines


def _lines_vm(vm):
    return [
        "SYNTHETIC SAMPLE VENDOR MASTER RECORD",
        f"Vendor Name: {vm['vendor_name']}",
        f"Tax ID: {vm['vendor_tax_id']}",
        f"Bank Account: {vm['bank_account']}",
    ]


def _lines_remittance(history, inv):
    h = history[0]
    return [
        "SYNTHETIC SAMPLE REMITTANCE ADVICE",
        f"Related Invoice: {h['invoice_number']}",
        f"Vendor Tax ID: {h['vendor_tax_id']}",
        f"Amount Paid: {h['amount']} {inv['currency']}",
        f"Payment Date: {h['payment_date']}",
    ]


def _lines_bank_notice(bank):
    return [
        "SYNTHETIC SAMPLE BANK ACCOUNT CHANGE NOTIFICATION",
        f"Old Bank Account: {bank['old_bank_account']}",
        f"New Bank Account: {bank['new_bank_account']}",
        f"Approval Status: {bank['approval_status']}",
        f"Verified By: {bank['verified_by']}",
    ]


def _apply_noise(lines, level, doc_tag):
    if level in (1, 3):
        lines += ["* SCANNED DOCUMENT — VERIFY AGAINST ORIGINAL *"]
    if level in (2, 3):
        lines += [f"Page 1 of 1 | scan-ref {doc_tag}-0001 | department copy"]


def render_pdf(path, lines):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 60), "\n".join(lines), fontsize=10)
    doc.set_metadata({"title": "Synthetic Track B document", "producer": "track-b-generator",
                      "creationDate": "", "modDate": ""})
    bytes_ = doc.tobytes()
    doc.close()
    # PyMuPDF embeds a random trailer /ID file identifier per run, sometimes
    # as pure hex, sometimes as a binary string with non-hex bytes. Either way
    # it breaks byte-level reproducibility of the frozen dataset. Replace the
    # whole /ID construct with a constant. This is byte-safe: the xref table
    # precedes the trailer, so no recorded offsets are invalidated.
    # Determinism is a freeze requirement (verified by verify_track_b.py).
    m = re.search(rb"/ID\[.*?\]>>", bytes_, re.DOTALL)
    if m:
        constant_id = b"/ID[<545241434B4242554C504F5359434C45><545241434B4242554C504F5359434C45>]>>"
        bytes_ = bytes_[:m.start()] + constant_id + bytes_[m.end():]
    path.write_bytes(bytes_)


def render_png(path, lines):
    width, height, line_h = 820, 60 + 16 * (len(lines) + 2), 16
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    y = 30
    for ln in lines:
        draw.text((30, y), ln, fill="black", font=font)
        y += line_h
    img.save(path, format="PNG", optimize=False)


def render_json(path, key, obj):
    path.write_text(json.dumps({key: obj}, indent=2) + "\n", encoding="utf-8", newline="\n")


def render_case(case_dir, canonical, spec):
    """Render all documents for one case; return bundle.json document list."""
    documents = []

    def out(name, renderer):
        renderer(case_dir / name)
        documents.append(name)

    out("invoice.pdf", lambda p: render_pdf(p, _lines_invoice(canonical["invoice"], spec)))

    if canonical["purchase_order"] is not None:
        if spec["po_format"] == "pdf":
            out("purchase_order.pdf",
                lambda p: render_pdf(p, _lines_po(canonical["purchase_order"], spec)))
        elif spec["po_format"] == "png":
            out("purchase_order.png",
                lambda p: render_png(p, _lines_po(canonical["purchase_order"], spec)))

    if canonical["goods_receipt"] is not None:
        if spec["grn_format"] == "pdf":
            out("goods_receipt.pdf", lambda p: render_pdf(p, _lines_grn(canonical["goods_receipt"])))
        elif spec["grn_format"] == "png":
            out("goods_receipt.png", lambda p: render_png(p, _lines_grn(canonical["goods_receipt"])))

    if canonical["vendor_master"] is not None:
        if spec["vm_format"] == "pdf":
            out("vendor_master.pdf", lambda p: render_pdf(p, _lines_vm(canonical["vendor_master"])))
        elif spec["vm_format"] == "json":
            out("vendor_master.json",
                lambda p: render_json(p, "vendor_master", canonical["vendor_master"]))

    if spec.get("history_doc") and canonical["prior_payment_history"]:
        out("remittance_advice.pdf",
            lambda p: render_pdf(p, _lines_remittance(canonical["prior_payment_history"],
                                                      canonical["invoice"])))

    if spec.get("bank_doc") and canonical["bank_change_evidence"]:
        out("bank_change_notice.pdf",
            lambda p: render_pdf(p, _lines_bank_notice(canonical["bank_change_evidence"])))

    return documents


# ---------------------------------------------------------------------------
# Freeze
# ---------------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def write_case_bundle(case_dir, case_id, documents):
    payload = {"case_id": case_id, "track": "B", "documents": documents}
    (case_dir / "bundle.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def generate():
    if fitz is None or Image is None:
        raise SystemExit("Track B generation requires PyMuPDF and Pillow (not installed).")

    canonical_by_case = canonical_cases()
    oracle = Phase1Oracle()

    if CASES_DIR.exists():
        raise SystemExit(
            "Refusing to generate into an existing data/track_b/cases/ tree. "
            "The dataset is frozen; regeneration requires explicit versioning."
        )

    manifest_rows = []
    for case_id in sorted(canonical_by_case):
        canonical = canonical_by_case[case_id]
        spec = RENDER_SPECS[case_id]

        # Official oracle derives the ground truth from the canonical bundle.
        recommendation, findings = oracle.evaluate(canonical)

        case_dir = CASES_DIR / case_id
        case_dir.mkdir(parents=True)
        documents = render_case(case_dir, canonical, spec)
        write_case_bundle(case_dir, case_id, documents)

        gt = {
            "case_id": case_id,
            "track": "B",
            "expected_recommendation": recommendation,
            "expected_findings": sorted(findings),
            "challenging": case_id == "case_111",
            "canonical": canonical,
            "render_spec": spec,
            "derived_by": "scripts/validate_phase1.Phase1Oracle (official rulebook logic, unmodified)",
        }
        GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
        gt_path = GROUND_TRUTH_DIR / f"{case_id}.json"
        gt_path.write_text(json.dumps(gt, indent=2) + "\n", encoding="utf-8", newline="\n")

        for doc in documents:
            manifest_rows.append((sha256_bytes((case_dir / doc).read_bytes()),
                                  f"cases/{case_id}/{doc}"))
        manifest_rows.append((sha256_bytes((case_dir / "bundle.json").read_bytes()),
                              f"cases/{case_id}/bundle.json"))
        manifest_rows.append((sha256_bytes(gt_path.read_bytes()),
                              f"ground_truth/{case_id}.json"))

    lines = [f"--- TRACK B MANIFEST {VERSION} ---"]
    lines += [f"{h}  {p}" for h, p in sorted(manifest_rows, key=lambda r: r[1])]
    MANIFEST_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"Track B v1.0 generated: {len(canonical_by_case)} cases, "
          f"{len(manifest_rows)} manifest entries.")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    generate()
