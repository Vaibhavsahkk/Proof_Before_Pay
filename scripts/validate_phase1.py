import json
import os
import glob
import re
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

import jsonschema

HOLD_FINDINGS = {
    "Currency Mismatch",
    "Duplicate Billing",
    "Math Error",
    "Price Contradiction",
    "Quantity Mismatch",
    "Tax Rate Contradiction",
    "Invalid Currency"
}

INVESTIGATE_FINDINGS = {
    "Duplicate GRN Line ID",
    "Duplicate Invoice Line ID",
    "Duplicate PO Line ID",
    "Missing GRN",
    "Missing GRN Line ID",
    "Missing PO",
    "Missing PO Line ID",
    "Missing Vendor Master",
    "Unverified Bank Change",
    "Vendor Identity Mismatch"
}

def validate_schemas():
    with open('benchmark/schemas/public_evidence_bundle.json') as f:
        public_schema = json.load(f)
    with open('benchmark/schemas/ground_truth.json') as f:
        gt_schema = json.load(f)
        
    public_files = sorted(glob.glob('data/cases/public/*.json'))
    gt_files = sorted(glob.glob('data/cases/ground_truth/*.json'))
    
    for pf in public_files:
        with open(pf) as f:
            jsonschema.validate(instance=json.load(f), schema=public_schema)
    for gf in gt_files:
        with open(gf) as f:
            jsonschema.validate(instance=json.load(f), schema=gt_schema)

def validate_cases_count():
    public_files = sorted(glob.glob('data/cases/public/*.json'))
    gt_files = sorted(glob.glob('data/cases/ground_truth/*.json'))
    assert len(public_files) == 6, f"Expected 6 public cases, found {len(public_files)}"
    assert len(gt_files) == 6, f"Expected 6 ground truth cases, found {len(gt_files)}"

    public_names = {Path(path).name for path in public_files}
    ground_truth_names = {Path(path).name for path in gt_files}
    assert public_names == ground_truth_names, "Public and ground-truth case filenames do not match"

    neutral_id_pattern = re.compile(r"^case_\d{3}$")
    for public_path in public_files:
        stem = Path(public_path).stem
        assert neutral_id_pattern.fullmatch(stem), f"Non-neutral public filename: {public_path}"
        ground_truth_path = Path('data/cases/ground_truth') / Path(public_path).name
        with open(public_path, encoding='utf-8') as public_file:
            public_data = json.load(public_file)
        with open(ground_truth_path, encoding='utf-8') as ground_truth_file:
            ground_truth_data = json.load(ground_truth_file)
        assert public_data['case_id'] == stem, f"Public case_id does not match filename: {public_path}"
        assert ground_truth_data['case_id'] == stem, f"Ground-truth case_id does not match filename: {ground_truth_path}"

def validate_leakage():
    public_files = sorted(glob.glob('data/cases/public/*.json'))
    
    # Treat punctuation and underscores as separators, while allowing ordinary
    # words such as "payment" that merely contain the letters "pay".
    pattern = re.compile(r'(?<![a-z0-9])(pay|hold|investigate)(?![a-z0-9])', re.IGNORECASE)
    
    answer_indicators = {
        "answerkey",
        "expectedfindings",
        "expectedrecommendation",
        "groundtruth",
        "label"
    }

    def contains_answer_indicator(value):
        normalized = re.sub(r"[^a-z0-9]+", "", str(value).lower())
        return next((term for term in answer_indicators if term in normalized), None)

    def check_leakage(obj, filepath):
        if isinstance(obj, dict):
            for k, v in obj.items():
                k_lower = str(k).lower()
                if pattern.search(k_lower):
                    assert False, f"Leakage detected! Found exact recommendation in key '{k}' in {filepath}"
                indicator = contains_answer_indicator(k_lower)
                if indicator:
                    assert False, f"Leakage detected! Found answer indicator '{indicator}' in key '{k}' in {filepath}"
                check_leakage(v, filepath)
        elif isinstance(obj, list):
            for item in obj:
                check_leakage(item, filepath)
        elif isinstance(obj, str):
            v_lower = obj.lower()
            if pattern.search(v_lower):
                assert False, f"Leakage detected! Found exact recommendation '{obj}' in {filepath}"
            indicator = contains_answer_indicator(v_lower)
            if indicator:
                assert False, f"Leakage detected! Found answer indicator '{indicator}' in {filepath}"
                    
    for pf in public_files:
        pf_lower = pf.lower()
        if contains_answer_indicator(pf_lower) or pattern.search(pf_lower):
            assert False, f"Leakage in filename/path: {pf}"
            
        with open(pf) as f:
            data = json.load(f)
            check_leakage(data, pf)

def validate_synthetic_constraints():
    synthetic_keywords = ["SYNTHETIC", "FAKECORP", "MOCK", "PSEUDO", "TESTAMENT"]
    public_files = sorted(glob.glob('data/cases/public/*.json'))
    for pf in public_files:
        with open(pf) as f:
            data = json.load(f)
            vendor_name = data['invoice']['vendor_name'].upper()
            assert any(k in vendor_name for k in synthetic_keywords), f"Non-synthetic vendor name detected in {pf}: {vendor_name}"

class Phase1Oracle:
    def evaluate(self, case_data):
        inv = case_data['invoice']
        po = case_data.get('purchase_order')
        grn = case_data.get('goods_receipt')
        vm = case_data.get('vendor_master')
        history = case_data.get('prior_payment_history') or []
        bank_change = case_data.get('bank_change_evidence')
        
        findings = []
        
        # Uniqueness checks
        inv_item_ids = [i['item_id'] for i in inv['items']]
        if len(inv_item_ids) != len(set(inv_item_ids)):
            findings.append("Duplicate Invoice Line ID")
        
        # 1. HOLD Conditions
        for h in history:
            if h['invoice_number'] == inv['invoice_number'] and h['vendor_tax_id'] == inv['vendor_tax_id'] and h['amount'] == inv['total']:
                findings.append("Duplicate Billing")
                break
                
        if grn:
            grn_item_ids = [i['item_id'] for i in grn['items']]
            if len(grn_item_ids) != len(set(grn_item_ids)):
                findings.append("Duplicate GRN Line ID")
                
            for inv_item in inv['items']:
                grn_item = next((i for i in grn['items'] if i['item_id'] == inv_item['item_id']), None)
                if grn_item:
                    if Decimal(inv_item['quantity']) > Decimal(grn_item['quantity_accepted']):
                        findings.append("Quantity Mismatch")
                else:
                    findings.append("Missing GRN Line ID")
                    
        if po:
            po_item_ids = [i['item_id'] for i in po['items']]
            if len(po_item_ids) != len(set(po_item_ids)):
                findings.append("Duplicate PO Line ID")
                
            for inv_item in inv['items']:
                po_item = next((i for i in po['items'] if i['item_id'] == inv_item['item_id']), None)
                if po_item:
                    if abs(Decimal(inv_item['unit_price']) - Decimal(po_item['unit_price'])) > Decimal('0.01'):
                        findings.append("Price Contradiction")
                else:
                    findings.append("Missing PO Line ID")
                    
            if inv['currency'] != po['currency']:
                findings.append("Currency Mismatch")
            if po['currency'] != "USD" and "Invalid Currency" not in findings:
                findings.append("Invalid Currency")

            if inv['tax_rate_percent'] != po['tax_rate_percent']:
                findings.append("Tax Rate Contradiction")

        if inv['currency'] != "USD" and "Invalid Currency" not in findings:
            findings.append("Invalid Currency")
                        
        # Math Error
        calculated_subtotal = Decimal('0.00')
        for item in inv['items']:
            qty = Decimal(item['quantity'])
            price = Decimal(item['unit_price'])
            line_total = (qty * price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if abs(line_total - Decimal(item['line_total'])) > Decimal('0.01'):
                if "Math Error" not in findings: findings.append("Math Error")
            calculated_subtotal += line_total
            
        if abs(calculated_subtotal - Decimal(inv['subtotal'])) > Decimal('0.01'):
            if "Math Error" not in findings: findings.append("Math Error")
            
        # Use authoritative tax from PO if exists, else Invoice
        authoritative_tax_rate = po['tax_rate_percent'] if po else inv['tax_rate_percent']
        tax_rate = Decimal(authoritative_tax_rate) / Decimal('100')
        expected_tax = (calculated_subtotal * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if abs(expected_tax - Decimal(inv['tax'])) > Decimal('0.01'):
            if "Math Error" not in findings: findings.append("Math Error")
            
        expected_total = calculated_subtotal + Decimal(inv['tax'])
        if abs(expected_total - Decimal(inv['total'])) > Decimal('0.01'):
            if "Math Error" not in findings: findings.append("Math Error")

        # 2. INVESTIGATE Conditions
        if vm:
            if inv['bank_account'] != vm['bank_account']:
                if not bank_change or bank_change['new_bank_account'] != inv['bank_account'] or bank_change['old_bank_account'] != vm['bank_account'] or bank_change['approval_status'] != "APPROVED":
                    findings.append("Unverified Bank Change")
            if inv['vendor_name'] != vm['vendor_name'] or inv['vendor_tax_id'] != vm['vendor_tax_id']:
                findings.append("Vendor Identity Mismatch")
        else:
            findings.append("Missing Vendor Master")
            
        if not po:
            findings.append("Missing PO")
        if not grn:
            findings.append("Missing GRN")

        # Recommendation logic
        # HOLD > INVESTIGATE > PAY
        has_hold = any(f in HOLD_FINDINGS for f in findings)
        has_investigate = any(f in INVESTIGATE_FINDINGS for f in findings)
        
        if has_hold:
            rec = "HOLD"
        elif has_investigate:
            rec = "INVESTIGATE"
        else:
            rec = "PAY"
            
        # Ensure deterministic order
        findings = sorted(list(set(findings)))
        return rec, findings

def validate_oracle():
    oracle = Phase1Oracle()
    public_files = sorted(glob.glob('data/cases/public/*.json'))
    
    print(f"{'Case ID':<35} | {'Derived Rec':<11} | {'Truth Rec':<11} | {'PASS':<5}")
    print("-" * 80)
    for pf in public_files:
        with open(pf, encoding='utf-8') as f:
            public_data = json.load(f)
        case_id = public_data['case_id']
        
        gt_path = Path(pf).parent.parent / 'ground_truth' / Path(pf).name
        with open(gt_path, encoding='utf-8') as f:
            gt_data = json.load(f)

        assert gt_data['case_id'] == case_id, f"Ground-truth case_id mismatch for {pf}"
            
        expected_rec = gt_data['expected_recommendation']
        expected_findings = sorted(gt_data['expected_findings'])
        
        derived_rec, derived_findings = oracle.evaluate(public_data)
        
        passed = (derived_rec == expected_rec) and (derived_findings == expected_findings)
        print(f"{case_id:<35} | {derived_rec:<11} | {expected_rec:<11} | {str(passed):<5}")
        
        if not passed:
            assert False, f"Oracle mismatch for {case_id}: Derived ({derived_rec}, {derived_findings}) != Expected ({expected_rec}, {expected_findings})"

def main():
    print("Starting Phase 1 Validation...")
    validate_cases_count()
    print("[PASS] Case count validation")
    validate_schemas()
    print("[PASS] Schema validation")
    validate_leakage()
    print("[PASS] Leakage validation")
    validate_synthetic_constraints()
    print("[PASS] Synthetic data validation")
    validate_oracle()
    print("[PASS] Oracle ground truth validation")
    print("ALL PHASE 1 VALIDATIONS PASSED")

if __name__ == '__main__':
    main()
