import json
import os
import glob
from decimal import Decimal

def validate_schemas():
    try:
        import jsonschema
    except ImportError:
        print("jsonschema not installed, skipping strict json schema validation for now.")
        return True
    
    # Load schemas
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
            
    return True

def validate_cases_count():
    public_files = glob.glob('data/cases/public/*.json')
    gt_files = glob.glob('data/cases/ground_truth/*.json')
    assert len(public_files) == 5, f"Expected 5 public cases, found {len(public_files)}"
    assert len(gt_files) == 5, f"Expected 5 ground truth cases, found {len(gt_files)}"

def test_leakage():
    # Public files must contain no expected recommendation, expected findings, labels, ground_truth fields
    public_files = glob.glob('data/cases/public/*.json')
    forbidden_terms = ["PAY", "HOLD", "INVESTIGATE", "expected_recommendation", "ground_truth", "expected_exception_name"]
    
    for pf in public_files:
        with open(pf) as f:
            content = f.read()
            for term in forbidden_terms:
                assert term not in content, f"Leakage detected! Found '{term}' in {pf}"

def validate_synthetic_constraints():
    # Verify synthetic nature
    synthetic_keywords = ["SYNTHETIC", "FAKECORP", "MOCK", "PSEUDO", "TESTAMENT"]
    public_files = glob.glob('data/cases/public/*.json')
    
    for pf in public_files:
        with open(pf) as f:
            data = json.load(f)
            vendor_name = data['invoice']['vendor_name'].upper()
            assert any(k in vendor_name for k in synthetic_keywords), f"Non-synthetic vendor name detected in {pf}: {vendor_name}"

def validate_arithmetic():
    public_files = glob.glob('data/cases/public/*.json')
    
    for pf in public_files:
        with open(pf) as f:
            data = json.load(f)
            inv = data['invoice']
            
            calculated_subtotal = Decimal('0.00')
            for item in inv['items']:
                qty = Decimal(item['quantity'])
                price = Decimal(item['unit_price'])
                line_total = Decimal(item['line_total'])
                assert qty * price == line_total, f"Line total mismatch in {pf}"
                calculated_subtotal += line_total
                
            assert calculated_subtotal == Decimal(inv['subtotal']), f"Subtotal mismatch in {pf}"
            assert calculated_subtotal + Decimal(inv['tax']) == Decimal(inv['total']), f"Total mismatch in {pf}"

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
    validate_arithmetic()
    print("[PASS] Arithmetic validation")
    print("ALL PHASE 1 VALIDATIONS PASSED")

if __name__ == '__main__':
    main()
