import io
import os
import json
import base64
import fitz

from src.agent.document_adapter import DocumentAdapter
from src.agent.orchestrator import AgentOrchestrator

def verify_smart_and_guided_flows():
    print("=" * 70)
    print("MASTER CASE / SMART REVIEW & GUIDED CASES INDEPENDENT AUDIT")
    print("=" * 70)

    orch = AgentOrchestrator()
    adapter = DocumentAdapter()

    # 1. VERIFY GUIDED CASES
    print("\n[STEP 1] Testing Guided / Example Cases Selection")
    guided_cases = ["case_001", "case_002", "case_004", "case_005"]
    for cid in guided_cases:
        filepath = f"data/cases/public/{cid}.json"
        with open(filepath, "r", encoding="utf-8") as f:
            raw_evidence = f.read()
        res = orch.run_workflow(cid, raw_evidence)
        print(f"  Guided Case '{cid}' -> Recommendation: {res['recommendation']} | Findings: {res['findings']}")
        assert res["recommendation"] in ["PAY", "HOLD", "INVESTIGATE"]
    print("  [PASS] All guided example cases operate cleanly.")

    # 2. VERIFY SMART REVIEW / MASTER CASE (Custom Document, No Anomaly Preselected)
    print("\n[STEP 2] Testing Smart Review (Master Automatic Document Review)")
    doc = fitz.open()
    page = doc.new_page()
    custom_pdf_text = (
        "INVOICE\n"
        "Invoice Number: INV-MASTER-99\n"
        "Vendor: GLOBAL LOGISTICS CORP\n"
        "Tax ID: TX-7777\n"
        "Bank Account: ACC-8888\n"
        "Currency: USD\n"
        "Tax Rate: 5.00%\n"
        "Item: FREIGHT-01, Qty: 2, Unit Price: 1500.00 USD, Total: 3000.00 USD\n"
        "Subtotal: 3000.00 USD, Tax: 150.00 USD, Total: 3150.00 USD\n\n"
        "PURCHASE ORDER: PO-MASTER-99\n"
        "Item: FREIGHT-01, Qty: 2, Price: 1500.00 USD\n\n"
        "GOODS RECEIPT: GRN-MASTER-99\n"
        "Item: FREIGHT-01, Accepted Qty: 2\n\n"
        "VENDOR MASTER RECORD\n"
        "Name: GLOBAL LOGISTICS CORP, Tax ID: TX-7777, Bank: ACC-8888"
    )
    page.insert_text((50, 50), custom_pdf_text, fontsize=10)
    pdf_bytes = doc.tobytes()
    doc.close()

    raw_pdf_evidence = adapter.process_file("freight_invoice.pdf", pdf_bytes, "application/pdf")
    res_smart = orch.run_workflow("case_000", raw_pdf_evidence)
    print(f"  Smart Review Input: freight_invoice.pdf (Raw PDF)")
    print(f"  Dynamic Recommendation: {res_smart['recommendation']}")
    print(f"  Dynamic Findings:       {res_smart['findings']}")
    print(f"  Verified Evidence:      {res_smart['evidence_references']}")
    print(f"  Calculations Executed:  {res_smart['deterministic_calculation_references']}")
    assert res_smart["recommendation"] == "PAY"
    assert res_smart["findings"] == []
    print("  [PASS] Smart Review automatically verified clean PDF document.")

    # 3. VERIFY MULTI-DOCUMENT SMART REVIEW
    print("\n[STEP 3] Testing Multi-Document Smart Review Ingestion")
    files = [
        {"name": "freight_inv.pdf", "data": pdf_bytes, "type": "application/pdf"},
        {"name": "vendor_master.json", "data": json.dumps({"vendor_master": {"vendor_name": "GLOBAL LOGISTICS CORP", "vendor_tax_id": "TX-7777", "bank_account": "ACC-8888"}}).encode(), "type": "application/json"}
    ]
    bundle_str, meta = adapter.process_bundle(files)
    res_multi = orch.run_workflow("case_000", bundle_str)
    print(f"  Multi-Doc Uploaded Files: {[m['name'] for m in meta]}")
    print(f"  Multi-Doc Recommendation: {res_multi['recommendation']}")
    assert len(meta) == 2
    assert res_multi["recommendation"] == "PAY"
    print("  [PASS] Multi-document Smart Review completed successfully.")

    # 4. VERIFY MULTI-FINDING PRESERVATION (Case 006)
    print("\n[STEP 4] Testing Multi-Finding Preservation (Case 006)")
    with open("data/cases/public/case_006.json", "r", encoding="utf-8") as f:
        c006_raw = f.read()
    res_006 = orch.run_workflow("case_006", c006_raw)
    print(f"  Case 006 Recommendation: {res_006['recommendation']}")
    print(f"  Case 006 Findings:       {res_006['findings']}")
    assert res_006["recommendation"] == "HOLD"
    assert "Duplicate Billing" in res_006["findings"]
    assert "Unverified Bank Change" in res_006["findings"]
    print("  [PASS] Multi-finding preservation verified.")

    # 5. VERIFY MISSING EVIDENCE REPORTING (Case 011)
    print("\n[STEP 5] Testing Missing Evidence Surfacing (Case 011)")
    with open("data/cases/public/case_011.json", "r", encoding="utf-8") as f:
        c011_raw = f.read()
    res_011 = orch.run_workflow("case_011", c011_raw)
    print(f"  Case 011 Recommendation: {res_011['recommendation']}")
    print(f"  Case 011 Missing Evid.:  {res_011['missing_evidence']}")
    assert res_011["recommendation"] == "INVESTIGATE"
    assert "Missing Vendor Master" in res_011["missing_evidence"]
    print("  [PASS] Missing evidence surfaced explicitly.")

    print("\n" + "=" * 70)
    print("ALL SMART REVIEW & GUIDED CASE FLOWS 100% VERIFIED")
    print("=" * 70)

if __name__ == "__main__":
    verify_smart_and_guided_flows()
