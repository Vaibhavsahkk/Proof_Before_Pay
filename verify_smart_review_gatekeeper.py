import io
import os
import json
import base64
import fitz
from PIL import Image

from src.agent.document_adapter import DocumentAdapter, DocumentProcessingError
from src.agent.orchestrator import AgentOrchestrator
from src.tools.calculator import DecimalCalculator
from src.tools.equality import EqualityChecker
from src.tools.rule_evaluator import RuleEvaluator

def run_gatekeeper_verification():
    print("================================================================")
    print("SMART REVIEW / AUTOMATIC ANOMALY DETECTION GATEKEEPER AUDIT")
    print("================================================================")

    adapter = DocumentAdapter()
    orch = AgentOrchestrator()

    # CHECK 1 & 2: User provides raw document without selecting anomaly
    print("\n--- CHECK 1 & 2: Automatic Anomaly Detection (No Anomaly Chosen by User) ---")
    doc = fitz.open()
    page = doc.new_page()
    raw_pdf_text = (
        "INVOICE\n"
        "Invoice Number: INV-8888\n"
        "Vendor: ACME INDUSTRIAL LLC\n"
        "Tax ID: TX-1111\n"
        "Bank Account: ACC-9999\n"
        "Currency: USD\n"
        "Tax Rate: 10.00%\n"
        "Item: PART-X, Qty: 10, Unit Price: 100.00 USD, Total: 1000.00 USD\n"
        "Subtotal: 1000.00 USD, Tax: 100.00 USD, Total: 1100.00 USD\n\n"
        "PURCHASE ORDER: PO-7777\n"
        "Item: PART-X, Qty: 10, Price: 80.00 USD\n\n" # Price Contradiction (100 vs 80)
        "GOODS RECEIPT: GRN-6666\n"
        "Item: PART-X, Accepted Qty: 10\n\n"
        "VENDOR MASTER RECORD\n"
        "Name: ACME INDUSTRIAL LLC, Tax ID: TX-1111, Bank: ACC-9999"
    )
    page.insert_text((50, 50), raw_pdf_text, fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()

    raw_evidence_pdf = adapter.process_file("supplier_bill.pdf", pdf_bytes, "application/pdf")
    res_pdf = orch.run_workflow("case_999", raw_evidence_pdf)
    print(f"  Document Provided: supplier_bill.pdf (User selected NO anomaly)")
    print(f"  Discovered Recommendation: {res_pdf['recommendation']}")
    print(f"  Discovered Findings:       {res_pdf['findings']}")
    assert res_pdf["recommendation"] in ["HOLD", "INVESTIGATE"], "Must automatically flag anomaly"
    assert len(res_pdf["findings"]) > 0, "Must automatically detect findings without user prompt"
    print("  [PASS] Automatic anomaly detection verified.")

    # CHECK 3 & 4: Multi-Document Support
    print("\n--- CHECK 3 & 4: Multi-Document Bundle Ingestion ---")
    files = [
        {"name": "invoice_doc.pdf", "data": pdf_bytes, "type": "application/pdf"},
        {"name": "vendor_record.json", "data": json.dumps({"vendor_master": {"vendor_name": "ACME INDUSTRIAL LLC", "vendor_tax_id": "TX-1111", "bank_account": "ACC-9999"}}).encode(), "type": "application/json"}
    ]
    bundle_str, meta = adapter.process_bundle(files)
    print(f"  Uploaded Files: {[m['name'] for m in meta]}")
    assert len(meta) == 2
    assert "=== DOCUMENT: invoice_doc.pdf" in bundle_str
    assert "vendor_master" in bundle_str
    print("  [PASS] Multi-document identities preserved and tagged.")

    # CHECK 5: Multi-Finding Preservation
    print("\n--- CHECK 5: Multi-Finding Preservation (No 'First Finding Wins') ---")
    with open("data/cases/public/case_006.json", "r", encoding="utf-8") as f:
        case_006_raw = f.read()
    res_006 = orch.run_workflow("case_006", case_006_raw)
    print(f"  Case 006 Recommendation: {res_006['recommendation']}")
    print(f"  Case 006 Findings:       {res_006['findings']}")
    assert res_006["recommendation"] == "HOLD"
    assert "Duplicate Billing" in res_006["findings"]
    assert "Unverified Bank Change" in res_006["findings"]
    print("  [PASS] Multi-finding preservation verified (both HOLD and INVESTIGATE findings returned).")

    # CHECK 6: Missing Evidence Reporting
    print("\n--- CHECK 6: Missing Evidence Reporting ---")
    with open("data/cases/public/case_011.json", "r", encoding="utf-8") as f:
        case_011_raw = f.read()
    res_011 = orch.run_workflow("case_011", case_011_raw)
    print(f"  Case 011 Recommendation: {res_011['recommendation']}")
    print(f"  Case 011 Findings:       {res_011['findings']}")
    print(f"  Case 011 Missing Evid.:  {res_011['missing_evidence']}")
    assert res_011["recommendation"] == "INVESTIGATE"
    assert "Missing Vendor Master" in res_011["findings"]
    assert "Missing Vendor Master" in res_011["missing_evidence"]
    print("  [PASS] Missing evidence surfaced explicitly.")

    # CHECK 7 & 8: Deterministic Tools & Pipeline Authoritativeness
    print("\n--- CHECK 7 & 8: Deterministic Engine Authoritativeness ---")
    mult_res = DecimalCalculator.multiply("10", "50.00")
    assert str(mult_res) == "500.00"
    eq_res = EqualityChecker.is_exact_match("TX-9999", "TX-9999")
    assert eq_res is True
    rule_res = RuleEvaluator.evaluate(["Duplicate Billing", "Unverified Bank Change"])
    assert rule_res["recommendation"] == "HOLD"
    print("  [PASS] Deterministic tools remain authoritative.")

    # CHECK 9: Agentic Depth & Trace Inspection
    print("\n--- CHECK 9: Agentic Depth & Pipeline Stages ---")
    trace_file = getattr(orch.logger, "log_file", None)
    print(f"  Active Trace File: {trace_file}")
    assert trace_file and os.path.exists(trace_file), "Trace file must exist"
    with open(trace_file, "r", encoding="utf-8") as tf:
        events = [json.loads(line.strip()) for line in tf if line.strip()]
    phases = [e.get("phase") for e in events]
    print(f"  Observed Pipeline Phases: {set(phases)}")
    assert "extract" in phases
    assert "verify" in phases
    assert "apply_rules" in phases
    assert "explain" in phases
    print("  [PASS] Genuine agentic pipeline executed.")

    # CHECK 10: Safe Error Handling
    print("\n--- CHECK 10: Safe Fail-Closed Error Handling ---")
    try:
        adapter.process_file("corrupted.pdf", b"BAD_DATA")
        assert False, "Should have raised DocumentProcessingError"
    except DocumentProcessingError as e:
        print(f"  Corrupted File Caught: {e}")
    print("  [PASS] Corrupted documents safely rejected / fail-closed.")

    print("\n================================================================")
    print("ALL GATEKEEPER CHECKS EXECUTED AND PASSED — 100%")
    print("================================================================")

if __name__ == "__main__":
    run_gatekeeper_verification()
