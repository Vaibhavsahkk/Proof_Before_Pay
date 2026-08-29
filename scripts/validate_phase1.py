import json
import os
import glob
from decimal import Decimal, ROUND_HALF_UP

import jsonschema

def validate_schemas():
    with open('benchmark/schemas/public_evidence_bundle.json') as f:
        public_schema = json.load(f)
    with open('benchmark/schemas/ground_truth.json') as f:
        gt_schema = json.load(f)
        
    public_files = glob.glob('data/cases/public/*.json')
    gt_files = glob.glob('data/cases/ground_truth/*.json')
    
    for pf in public_files:
        with open(pf) as f:
            jsonschema.validate(instance=json.load(f), schema=public_schema)
    for gf in gt_files:
        with open(gf) as f:
            jsonschema.validate(instance=json.load(f), schema=gt_schema)

def validate_cases_count():
    public_files = glob.glob('data/cases/public/*.json')
    gt_files = glob.glob('data/cases/ground_truth/*.json')
    assert len(public_files) == 5, f"Expected 5 public cases, found {len(public_files)}"
    assert len(gt_files) == 5, f"Expected 5 ground truth cases, found {len(gt_files)}"

def test_leakage():
    public_files = glob.glob('data/cases/public/*.json')
    forbidden_terms = ["pay", "hold", "investigate", "expected_recommendation", "ground_truth", "expected_exception_name"]
    
    def check_leakage(obj, filepath):
        if isinstance(obj, dict):
            for k, v in obj.items():
                k_lower = str(k).lower()
                if k_lower in ["pay", "hold", "investigate"]:
                    assert False, f"Leakage detected! Found exact recommendation in key '{k}' in {filepath}"
                for term in ["expected_recommendation", "ground_truth", "expected_exception_name", "answer-key", "label"]:
                    if term in k_lower:
                        assert False, f"Leakage detected! Found '{term}' in key '{k}' in {filepath}"
                check_leakage(v, filepath)
        elif isinstance(obj, list):
            for item in obj:
                check_leakage(item, filepath)
        elif isinstance(obj, str):
            v_lower = obj.lower()
            if v_lower in ["pay", "hold", "investigate"]:
                assert False, f"Leakage detected! Found exact recommendation '{obj}' in {filepath}"
            for term in ["expected_recommendation", "ground_truth", "expected_exception_name", "answer-key", "label"]:
                if term in v_lower:
                    assert False, f"Leakage detected! Found '{term}' in {filepath}"
                    
    for pf in public_files:
        # Also check path
        pf_lower = pf.lower()
        if "ground_truth" in pf_lower or "expected" in pf_lower:
            assert False, f"Leakage in filename/path: {pf}"
            
        with open(pf) as f:
            data = json.load(f)
            check_leakage(data, pf)

def validate_synthetic_constraints():
    synthetic_keywords = ["SYNTHETIC", "FAKECORP", "MOCK", "PSEUDO", "TESTAMENT"]
    public_files = glob.glob('data/cases/public/*.json')
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
        
        # 1. HOLD Conditions
        # Duplicate Invoice
        for h in history:
            if h['invoice_number'] == inv['invoice_number'] and h['vendor_tax_id'] == inv['vendor_tax_id'] and h['amount'] == inv['total']:
                return "HOLD", "Duplicate Billing"
                
        # GRN Quantity Mismatch
        if grn:
            for inv_item in inv['items']:
                grn_item = next((i for i in grn['items'] if i['item_id'] == inv_item['item_id']), None)
                if grn_item:
                    if Decimal(inv_item['quantity']) > Decimal(grn_item['quantity_accepted']):
                        return "HOLD", "Quantity Mismatch"
        
        # PO Price Contradiction
        if po:
            for inv_item in inv['items']:
                po_item = next((i for i in po['items'] if i['item_id'] == inv_item['item_id']), None)
                if po_item:
                    if abs(Decimal(inv_item['unit_price']) - Decimal(po_item['unit_price'])) > Decimal('0.01'):
                        return "HOLD", "Price Contradiction"
                        
        # Check math
        calculated_subtotal = Decimal('0.00')
        for item in inv['items']:
            qty = Decimal(item['quantity'])
            price = Decimal(item['unit_price'])
            line_total = (qty * price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if abs(line_total - Decimal(item['line_total'])) > Decimal('0.01'):
                return "HOLD", "Math Error"
            calculated_subtotal += line_total
            
        if abs(calculated_subtotal - Decimal(inv['subtotal'])) > Decimal('0.01'):
            return "HOLD", "Math Error"
            
        tax_rate = Decimal(inv['tax_rate_percent']) / Decimal('100')
        expected_tax = (calculated_subtotal * tax_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if abs(expected_tax - Decimal(inv['tax'])) > Decimal('0.01'):
            return "HOLD", "Math Error"
            
        expected_total = calculated_subtotal + Decimal(inv['tax'])
        if abs(expected_total - Decimal(inv['total'])) > Decimal('0.01'):
            return "HOLD", "Math Error"

        # 2. INVESTIGATE Conditions
        if vm:
            if inv['bank_account'] != vm['bank_account']:
                if not bank_change or bank_change['new_bank_account'] != inv['bank_account']:
                    return "INVESTIGATE", "Unverified Bank Change"
            if inv['vendor_name'] != vm['vendor_name'] or inv['vendor_tax_id'] != vm['vendor_tax_id']:
                return "INVESTIGATE", "Vendor Identity Mismatch"
        else:
            return "INVESTIGATE", "Missing Vendor Master"
            
        if not po:
            return "INVESTIGATE", "Missing PO"
        if not grn:
            return "INVESTIGATE", "Missing GRN"

        # 3. PAY Condition
        return "PAY", None

def validate_oracle():
    oracle = Phase1Oracle()
    public_files = glob.glob('data/cases/public/*.json')
    
    print(f"{'Case ID':<35} | {'Derived':<15} | {'Ground Truth':<15} | {'PASS':<5}")
    print("-" * 80)
    for pf in public_files:
        with open(pf) as f:
            public_data = json.load(f)
        case_id = public_data['case_id']
        
        gt_path = pf.replace('public', 'ground_truth')
        with open(gt_path) as f:
            gt_data = json.load(f)
            
        expected_rec = gt_data['expected_recommendation']
        expected_exc = gt_data['expected_exception_name']
        
        derived_rec, derived_exc = oracle.evaluate(public_data)
        
        passed = (derived_rec == expected_rec) and (derived_exc == expected_exc)
        print(f"{case_id:<35} | {derived_rec:<15} | {expected_rec:<15} | {str(passed):<5}")
        
        if not passed:
            assert False, f"Oracle mismatch for {case_id}: Derived ({derived_rec}, {derived_exc}) != Expected ({expected_rec}, {expected_exc})"

def main():
    print("Starting Phase 1 Validation...")
    validate_cases_count()
    print("[PASS] Case count validation")
    validate_schemas()
    print("[PASS] Schema validation")
    test_leakage()
    print("[PASS] Leakage validation")
    validate_synthetic_constraints()
    print("[PASS] Synthetic data validation")
    validate_oracle()
    print("[PASS] Oracle ground truth validation")
    print("ALL PHASE 1 VALIDATIONS PASSED")

if __name__ == '__main__':
    main()
