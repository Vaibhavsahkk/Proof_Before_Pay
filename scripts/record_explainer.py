from pathlib import Path
import json
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "media"
RAW = MEDIA / "raw"
URL = "http://127.0.0.1:8080/"


def demo_response():
    return {
        "result": {
            "case_id": "case_004",
            "recommendation": "HOLD",
            "findings": ["Price Contradiction", "Math Error"],
            "evidence_references": ["invoice", "purchase_order", "goods_receipt", "vendor_master"],
            "deterministic_calculation_references": ["calculator.multiply", "calculator.check_equality", "calculator.sum_values"],
            "missing_evidence": [],
            "uncertainty": "The invoice price is higher than the approved purchase order price.",
            "required_human_next_step": "Hold payment and ask a human reviewer to confirm the price discrepancy with the supplier."
        },
        "extracted_data": {
            "vendor_master": {"vendor_name": "Northwind Industrial Supply", "vendor_tax_id": "TAX-2048", "bank_account": "****1842"},
            "invoice": {"invoice_number": "INV-004-2026", "total": "12840.00", "currency": "USD"}
        },
        "recovery_info": {"failover_occurred": False, "pool_exhausted": False, "slots": []},
        "checks_performed": ["Invoice math and totals", "Vendor Identity", "Purchase Order matching", "Goods Receipt matching", "Duplicate Billing"],
        "checks_skipped": [],
        "trace_file": "traces/raw/demo_case_004.jsonl"
    }


def demo_trace():
    events = [
        {"phase": "extract", "tool": "llm_extractor", "action": "observe_and_extract", "result": "SUCCESS"},
        {"phase": "verify", "tool": "calculator_equality", "action": "run_deterministic_checks", "result": "SUCCESS"},
        {"phase": "apply_rules", "tool": "rule_evaluator", "action": "evaluate_rules", "result": "SUCCESS"},
        {"phase": "explain", "tool": "llm_extractor", "action": "generate_explanation", "result": "SUCCESS"},
        {"phase": "validate", "tool": "jsonschema", "action": "validate_output_schema", "result": "SUCCESS"},
        {"phase": "escalate", "tool": "human", "action": "human_checkpoint", "result": "ESCALATED"},
    ]
    return {"trace_file": "traces/raw/demo_case_004.jsonl", "events": events}


def capture():
    MEDIA.mkdir(exist_ok=True)
    RAW.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(RAW))
        page = context.new_page()
        page.route("**/api/investigate", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(demo_response())))
        page.route("**/api/trace**", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(demo_trace())))

        architecture = (MEDIA / "architecture.svg").read_text(encoding="utf-8")
        page.set_content(architecture)
        page.screenshot(path=str(MEDIA / "01_architecture.png"), full_page=True)
        page.wait_for_timeout(10000)

        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")
        page.screenshot(path=str(MEDIA / "02_intake.png"), full_page=True)
        page.get_by_role("button", name="Select Case 004: Price Mismatch").click()
        page.screenshot(path=str(MEDIA / "03_case_selected.png"), full_page=True)
        page.get_by_role("button", name="Start Reviewing Payment").click()
        page.screenshot(path=str(MEDIA / "04_progress.png"), full_page=True)
        page.wait_for_timeout(1800)
        page.screenshot(path=str(MEDIA / "05_result.png"), full_page=True)
        page.get_by_role("tab", name="Automated Checks").click()
        page.screenshot(path=str(MEDIA / "06_automated_checks.png"), full_page=True)
        page.get_by_role("tab", name="Audit & Connection Log").click()
        page.screenshot(path=str(MEDIA / "07_audit_trace.png"), full_page=True)
        page.wait_for_timeout(12000)
        video_path = page.video.path()
        context.close()
        browser.close()
        final_video = MEDIA / "ui_walkthrough.webm"
        Path(video_path).replace(final_video)
        print(final_video)


if __name__ == "__main__":
    capture()