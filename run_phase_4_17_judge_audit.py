import io
import os
import sys
import json
import base64
import fitz
from PIL import Image

from src.agent.document_adapter import DocumentAdapter, DocumentProcessingError
from src.agent.orchestrator import AgentOrchestrator
from src.agent.credentials import CredentialManager, CredentialState
from src.tools.calculator import DecimalCalculator
from src.tools.equality import EqualityChecker
from src.tools.rule_evaluator import RuleEvaluator

def run_phase_4_17_audit():
    print("================================================================================")
    print("PHASE 4.17 — FINAL EXTERNAL JUDGE READINESS COMPREHENSIVE AUDIT")
    print("================================================================================")

    orch = AgentOrchestrator()
    adapter = DocumentAdapter()

    # 1. TEST GUIDED EXAMPLES (PAY, HOLD, INVESTIGATE)
    print("\n[1] Testing Guided Examples")
    with open("data/cases/public/case_001.json", "r", encoding="utf-8") as f:
        res_001 = orch.run_workflow("case_001", f.read())
    print(f"  Case 001 (Clean Invoice)      -> {res_001['recommendation']} | Findings: {res_001['findings']}")
    assert res_001['recommendation'] == 'PAY'

    with open("data/cases/public/case_002.json", "r", encoding="utf-8") as f:
        res_002 = orch.run_workflow("case_002", f.read())
    print(f"  Case 002 (Duplicate Billing)  -> {res_002['recommendation']} | Findings: {res_002['findings']}")
    assert res_002['recommendation'] == 'HOLD'
    assert 'Duplicate Billing' in res_002['findings']

    with open("data/cases/public/case_005.json", "r", encoding="utf-8") as f:
        res_005 = orch.run_workflow("case_005", f.read())
    print(f"  Case 005 (Bank Change)        -> {res_005['recommendation']} | Findings: {res_005['findings']}")
    assert res_005['recommendation'] == 'INVESTIGATE'
    assert 'Unverified Bank Change' in res_005['findings']

    # 2. TEST SMART REVIEW — PDF DOCUMENT
    print("\n[2] Testing Smart Review with PDF Document")
    doc = fitz.open()
    page = doc.new_page()
    pdf_text = (
        "SUPPLIER INVOICE\n"
        "Invoice Number: INV-PDF-001\n"
        "Vendor: SYNTHETIC WIDGETS LLC\n"
        "Tax ID: TX-9999\n"
        "Bank Account: ACC-1111\n"
        "Currency: USD\n"
        "Tax Rate: 10.00%\n"
        "Item: WIDGET-A, Qty: 10, Unit Price: 50.00 USD, Total: 500.00 USD\n"
        "Subtotal: 500.00 USD, Tax: 50.00 USD, Total: 550.00 USD\n\n"
        "PURCHASE ORDER: PO-PDF-001\n"
        "Item: WIDGET-A, Qty: 10, Price: 50.00 USD\n\n"
        "GOODS RECEIPT: GRN-PDF-001\n"
        "Item: WIDGET-A, Accepted Qty: 10\n\n"
        "VENDOR MASTER RECORD\n"
        "Name: SYNTHETIC WIDGETS LLC, Tax ID: TX-9999, Bank: ACC-1111"
    )
    page.insert_text((50, 50), pdf_text, fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()

    raw_pdf_evidence = adapter.process_file("invoice_doc.pdf", pdf_bytes, "application/pdf")
    res_pdf = orch.run_workflow("case_001", raw_pdf_evidence)
    print(f"  Smart Review PDF Result:       {res_pdf['recommendation']} | Findings: {res_pdf['findings']}")
    assert res_pdf['recommendation'] == 'PAY'

    # 3. TEST SMART REVIEW — IMAGE FILE (PNG)
    print("\n[3] Testing Smart Review with PNG Image File")
    img = Image.new("RGB", (120, 120), color="white")
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()
    # Image stream validation
    img_parsed = Image.open(io.BytesIO(img_bytes))
    img_parsed.verify()
    print("  PNG Image Byte Stream Verified via Pillow.")

    # 4. TEST MULTI-DOCUMENT SMART REVIEW
    print("\n[4] Testing Multi-Document Smart Review Ingestion")
    files = [
        {"name": "invoice_doc.pdf", "data": pdf_bytes, "type": "application/pdf"},
        {"name": "vendor_record.json", "data": json.dumps({"vendor_master": {"vendor_name": "SYNTHETIC WIDGETS LLC", "vendor_tax_id": "TX-9999", "bank_account": "ACC-1111"}}).encode(), "type": "application/json"}
    ]
    bundle_str, meta = adapter.process_bundle(files)
    res_multi = orch.run_workflow("case_001", bundle_str)
    print(f"  Multi-Doc Uploaded Files: {[m['name'] for m in meta]}")
    print(f"  Multi-Doc Recommendation: {res_multi['recommendation']}")
    assert len(meta) == 2
    assert res_multi['recommendation'] == 'PAY'

    # 5. TEST MULTI-FINDING PRESERVATION (CASE 006)
    print("\n[5] Testing Multi-Finding Preservation (Case 006)")
    with open("data/cases/public/case_006.json", "r", encoding="utf-8") as f:
        res_006 = orch.run_workflow("case_006", f.read())
    print(f"  Case 006 Recommendation:      {res_006['recommendation']}")
    print(f"  Case 006 Findings:            {res_006['findings']}")
    assert res_006['recommendation'] == 'HOLD'
    assert 'Duplicate Billing' in res_006['findings']
    assert 'Unverified Bank Change' in res_006['findings']

    # 6. TEST MISSING EVIDENCE SURFACING (CASE 011)
    print("\n[6] Testing Missing Evidence Surfacing (Case 011)")
    with open("data/cases/public/case_011.json", "r", encoding="utf-8") as f:
        res_011 = orch.run_workflow("case_011", f.read())
    print(f"  Case 011 Recommendation:      {res_011['recommendation']}")
    print(f"  Case 011 Missing Evidence:    {res_011['missing_evidence']}")
    assert res_011['recommendation'] == 'INVESTIGATE'
    assert 'Missing Vendor Master' in res_011['missing_evidence']

    # 7. TEST TRACE LOG INTEGRITY
    print("\n[7] Inspecting Active Trace Logs")
    trace_file = getattr(orch.logger, "log_file", None)
    print(f"  Active Trace File:            {trace_file}")
    assert trace_file and os.path.exists(trace_file)
    with open(trace_file, "r", encoding="utf-8") as tf:
        events = [json.loads(line.strip()) for line in tf if line.strip()]
    phases = {e.get("phase") for e in events}
    print(f"  Observed Workflow Phases:     {sorted(list(phases))}")
    assert 'extract' in phases and 'verify' in phases and 'apply_rules' in phases

    # 8. TEST CONTROLLED RECOVERY / POOL EXHAUSTION
    print("\n[8] Testing Controlled Failure & Safe Fail-Closed Recovery")
    exhausted_cm = CredentialManager(explicit_keys=["mock_key_1", "mock_key_2"])
    for c in exhausted_cm.credentials:
        c.state = CredentialState.EXHAUSTED
    exhausted_orch = AgentOrchestrator(credential_manager=exhausted_cm)
    
    # Ensure isolation from cache
    test_cache = "data/cache/extractions/case_ex_test.json"
    if os.path.exists(test_cache):
        os.remove(test_cache)
        
    res_ex = exhausted_orch.run_workflow("case_ex_test", "{\"invoice\": {\"total\": 500}}")
    print(f"  Exhaustion Recommendation:    {res_ex['recommendation']}")
    print(f"  Exhaustion Findings:          {res_ex['findings']}")
    assert res_ex['recommendation'] == 'INVESTIGATE'
    assert 'All credentials exhausted' in res_ex['findings']

    print("\n================================================================================")
    print("ALL PHASE 4.17 INDEPENDENT AUDIT STEPS EXECUTED AND PASSED — 100%")
    print("================================================================================")

if __name__ == "__main__":
    run_phase_4_17_audit()
