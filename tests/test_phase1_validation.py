import pytest
import os
import json
from decimal import Decimal

# Test the Phase 1 validation assertions themselves (positive and negative/adversarial cases).

def test_leakage_validator_fails_on_leakage(tmp_path):
    from scripts.validate_phase1 import test_leakage
    
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    
    with open(cases_dir / "case_leak.json", "w") as f:
        f.write('{"invoice_number": "INV-1001", "some_key": "PAY"}')
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json':
            return [str(cases_dir / "case_leak.json")]
        return []
    
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            test_leakage()
        assert "Leakage detected!" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_leakage_validator_fails_on_key_leakage(tmp_path):
    from scripts.validate_phase1 import test_leakage
    
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    
    with open(cases_dir / "case_leak2.json", "w") as f:
        f.write('{"expected_recommendation": "INV-1001"}')
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json':
            return [str(cases_dir / "case_leak2.json")]
        return []
    
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            test_leakage()
        assert "Leakage detected!" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_oracle_mutation_rejection(tmp_path):
    from scripts.validate_phase1 import validate_oracle
    
    public_dir = tmp_path / "data" / "cases" / "public"
    gt_dir = tmp_path / "data" / "cases" / "ground_truth"
    public_dir.mkdir(parents=True)
    gt_dir.mkdir(parents=True)
    
    # Clean case but we falsely label it HOLD
    public_data = {
        "case_id": "test_case",
        "invoice": {
            "invoice_number": "1", "vendor_name": "SYNTH", "vendor_tax_id": "1",
            "bank_account": "1", "currency": "USD", "tax_rate_percent": "0.00",
            "items": [{"item_id": "1", "description": "A", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"}],
            "subtotal": "1.00", "tax": "0.00", "total": "1.00"
        },
        "purchase_order": {"po_number": "1", "items": [{"item_id": "1", "quantity": "1", "unit_price": "1.00"}]},
        "goods_receipt": {"grn_number": "1", "items": [{"item_id": "1", "quantity_accepted": "1"}]},
        "vendor_master": {"vendor_name": "SYNTH", "vendor_tax_id": "1", "bank_account": "1"},
        "prior_payment_history": [],
        "bank_change_evidence": None
    }
    
    gt_data = {
        "case_id": "test_case",
        "expected_recommendation": "HOLD",
        "expected_exception_name": "Duplicate Billing"
    }
    
    with open(public_dir / "test_case.json", "w") as f: json.dump(public_data, f)
    with open(gt_dir / "test_case.json", "w") as f: json.dump(gt_data, f)
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json':
            return [str(public_dir / "test_case.json")]
        return []
        
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        # To avoid the gt glob we just patch it implicitly via the loop over public files in oracle
        with pytest.raises(AssertionError) as exc:
            validate_oracle()
        assert "Oracle mismatch for test_case" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_oracle_precedence(tmp_path):
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    
    # Setup a case that has both a Duplicate Billing (HOLD) and a Missing PO (INVESTIGATE)
    # The oracle should return HOLD (Duplicate Billing) due to precedence.
    public_data = {
        "case_id": "precedence_case",
        "invoice": {
            "invoice_number": "1", "vendor_name": "SYNTH", "vendor_tax_id": "1",
            "bank_account": "1", "currency": "USD", "tax_rate_percent": "0.00",
            "items": [{"item_id": "1", "description": "A", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"}],
            "subtotal": "1.00", "tax": "0.00", "total": "1.00"
        },
        "purchase_order": None, # Triggers INVESTIGATE
        "goods_receipt": {"grn_number": "1", "items": [{"item_id": "1", "quantity_accepted": "1"}]},
        "vendor_master": {"vendor_name": "SYNTH", "vendor_tax_id": "1", "bank_account": "1"},
        "prior_payment_history": [{"invoice_number": "1", "vendor_tax_id": "1", "amount": "1.00", "payment_date": "2025-01-01"}], # Triggers HOLD
        "bank_change_evidence": None
    }
    
    rec, exc = oracle.evaluate(public_data)
    assert rec == "HOLD"
    assert exc == "Duplicate Billing"

def test_schema_validator_fails_invalid_schema():
    from scripts.validate_phase1 import validate_schemas
    import jsonschema
    
    # We will pass invalid instance to the loaded schema.
    with open('benchmark/schemas/public_evidence_bundle.json') as f:
        public_schema = json.load(f)
        
    invalid_data = {
        "case_id": "1",
        "invoice": {
            "invoice_number": "1",
            "vendor_name": "V",
            "vendor_tax_id": "1",
            "bank_account": "1",
            "currency": "USD",
            "tax_rate_percent": "0", # Invalid pattern! Needs to be 0.00
            "items": [{"item_id": "1", "description": "A", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"}],
            "subtotal": "1.00", "tax": "0.00", "total": "1.00"
        },
        "purchase_order": None,
        "goods_receipt": None,
        "vendor_master": None,
        "prior_payment_history": None,
        "bank_change_evidence": None
    }
    
    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=public_schema)
