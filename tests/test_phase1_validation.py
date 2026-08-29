import pytest
import os
import json
from decimal import Decimal

def test_leakage_validator_fails_on_leakage(tmp_path):
    from scripts.validate_phase1 import validate_leakage
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    with open(cases_dir / "case_leak.json", "w") as f:
        f.write('{"invoice_number": "INV-1001", "some_key": "PAY"}')
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json': return [str(cases_dir / "case_leak.json")]
        return []
    
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            validate_leakage()
        assert "Leakage detected!" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_leakage_validator_fails_on_key_leakage(tmp_path):
    from scripts.validate_phase1 import validate_leakage
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    with open(cases_dir / "case_leak2.json", "w") as f:
        f.write('{"answer_key": "INV-1001"}')
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json': return [str(cases_dir / "case_leak2.json")]
        return []
    
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            validate_leakage()
        assert "Leakage detected!" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_leakage_validator_fails_on_filename_leakage(tmp_path):
    from scripts.validate_phase1 import validate_leakage
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    with open(cases_dir / "case_pay_something.json", "w") as f:
        f.write('{"invoice_number": "INV-1001"}')
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json': return [str(cases_dir / "case_pay_something.json")]
        return []
    
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            validate_leakage()
        assert "Leakage in filename/path" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_leakage_validator_fails_on_case_id_leakage(tmp_path):
    from scripts.validate_phase1 import validate_leakage
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    with open(cases_dir / "case_001.json", "w") as f:
        f.write('{"case_id": "case_pay"}')
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json': return [str(cases_dir / "case_001.json")]
        return []
    
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            validate_leakage()
        assert "Leakage detected!" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def test_oracle_mutation_rejection(tmp_path):
    from scripts.validate_phase1 import validate_oracle
    public_dir = tmp_path / "data" / "cases" / "public"
    gt_dir = tmp_path / "data" / "cases" / "ground_truth"
    public_dir.mkdir(parents=True)
    gt_dir.mkdir(parents=True)
    
    public_data = {
        "case_id": "test_case",
        "invoice": {
            "invoice_number": "1", "vendor_name": "SYNTH", "vendor_tax_id": "1",
            "bank_account": "1", "currency": "USD", "tax_rate_percent": "0.00",
            "items": [{"item_id": "1", "description": "A", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"}],
            "subtotal": "1.00", "tax": "0.00", "total": "1.00"
        },
        "purchase_order": {"po_number": "1", "currency": "USD", "tax_rate_percent": "0.00", "items": [{"item_id": "1", "quantity": "1", "unit_price": "1.00"}]},
        "goods_receipt": {"grn_number": "1", "items": [{"item_id": "1", "quantity_accepted": "1"}]},
        "vendor_master": {"vendor_name": "SYNTH", "vendor_tax_id": "1", "bank_account": "1"},
        "prior_payment_history": [],
        "bank_change_evidence": None
    }
    
    gt_data = {
        "case_id": "test_case",
        "expected_recommendation": "HOLD",
        "expected_findings": ["Duplicate Billing"]
    }
    
    with open(public_dir / "test_case.json", "w") as f: json.dump(public_data, f)
    with open(gt_dir / "test_case.json", "w") as f: json.dump(gt_data, f)
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json': return [str(public_dir / "test_case.json")]
        return []
        
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            validate_oracle()
        assert "Oracle mismatch for test_case" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob

def get_base_case():
    return {
        "case_id": "test_case",
        "invoice": {
            "invoice_number": "1", "vendor_name": "SYNTH", "vendor_tax_id": "1",
            "bank_account": "1", "currency": "USD", "tax_rate_percent": "0.00",
            "items": [{"item_id": "1", "description": "A", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"}],
            "subtotal": "1.00", "tax": "0.00", "total": "1.00"
        },
        "purchase_order": {"po_number": "1", "currency": "USD", "tax_rate_percent": "0.00", "items": [{"item_id": "1", "quantity": "1", "unit_price": "1.00"}]},
        "goods_receipt": {"grn_number": "1", "items": [{"item_id": "1", "quantity_accepted": "1"}]},
        "vendor_master": {"vendor_name": "SYNTH", "vendor_tax_id": "1", "bank_account": "1"},
        "prior_payment_history": [],
        "bank_change_evidence": None
    }

def test_oracle_clean_pay():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    rec, findings = oracle.evaluate(get_base_case())
    assert rec == "PAY"
    assert findings == []

def test_oracle_duplicate_hold():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["prior_payment_history"] = [{"invoice_number": "1", "vendor_tax_id": "1", "amount": "1.00", "payment_date": "2025"}]
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert findings == ["Duplicate Billing"]

def test_oracle_quantity_mismatch_hold():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["items"][0]["quantity"] = "2" # Exceeds GRN's 1
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert "Quantity Mismatch" in findings

def test_oracle_price_hold():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["items"][0]["unit_price"] = "1.50"
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert "Price Contradiction" in findings

def test_oracle_tax_hold():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["purchase_order"]["tax_rate_percent"] = "10.00" # Expected tax 0.10, but invoice has 0.00
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert "Math Error" in findings
    assert "Tax Rate Contradiction" in findings

    case = get_base_case()
    case["invoice"]["currency"] = "EUR"
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert "Currency Mismatch" in findings

def test_oracle_subtotal_total_hold():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["total"] = "999.00"
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert "Math Error" in findings

def test_oracle_missing_po_investigate():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["purchase_order"] = None
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Missing PO" in findings

def test_oracle_identity_mismatch():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["vendor_name"] = "OTHER"
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Vendor Identity Mismatch" in findings

def test_oracle_unverified_bank_change():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["bank_account"] = "999"
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Unverified Bank Change" in findings

    # An approved change with a mismatched old account is also unverified.
    case["bank_change_evidence"] = {"old_bank_account": "wrong", "new_bank_account": "999", "approval_status": "APPROVED", "verified_by": "System"}
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Unverified Bank Change" in findings
    
    # Adding pending bank change evidence
    case["bank_change_evidence"] = {"old_bank_account": "1", "new_bank_account": "999", "approval_status": "PENDING", "verified_by": "System"}
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Unverified Bank Change" in findings

def test_oracle_verified_bank_change():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["bank_account"] = "999"
    case["bank_change_evidence"] = {"old_bank_account": "1", "new_bank_account": "999", "approval_status": "APPROVED", "verified_by": "System"}
    rec, findings = oracle.evaluate(case)
    assert rec == "PAY"
    assert findings == []

def test_oracle_precedence():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["purchase_order"] = None # INVESTIGATE
    case["prior_payment_history"] = [{"invoice_number": "1", "vendor_tax_id": "1", "amount": "1.00", "payment_date": "2025"}] # HOLD
    rec, findings = oracle.evaluate(case)
    assert rec == "HOLD"
    assert "Duplicate Billing" in findings
    assert "Missing PO" in findings

def test_oracle_missing_line_ids():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["items"].append({"item_id": "2", "description": "B", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"})
    case["invoice"]["subtotal"] = "2.00"
    case["invoice"]["total"] = "2.00"
    # PO and GRN only have "1", so "2" is missing.
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Missing PO Line ID" in findings
    assert "Missing GRN Line ID" in findings

def test_oracle_duplicate_line_ids():
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    case = get_base_case()
    case["invoice"]["items"].append({"item_id": "1", "description": "B", "quantity": "1", "unit_price": "1.00", "line_total": "1.00"})
    case["invoice"]["subtotal"] = "2.00"
    case["invoice"]["total"] = "2.00"
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Duplicate Invoice Line ID" in findings

    case = get_base_case()
    case["purchase_order"]["items"].append(dict(case["purchase_order"]["items"][0]))
    case["goods_receipt"]["items"].append(dict(case["goods_receipt"]["items"][0]))
    rec, findings = oracle.evaluate(case)
    assert rec == "INVESTIGATE"
    assert "Duplicate PO Line ID" in findings
    assert "Duplicate GRN Line ID" in findings

def test_schema_validator_fails_invalid_schema():
    from scripts.validate_phase1 import HOLD_FINDINGS, INVESTIGATE_FINDINGS, validate_schemas
    import jsonschema
    with open('benchmark/schemas/public_evidence_bundle.json') as f:
        public_schema = json.load(f)
    invalid_data = get_base_case()
    invalid_data["invoice"]["tax_rate_percent"] = "0" # Invalid pattern
    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=public_schema)

    invalid_data = get_base_case()
    invalid_data["case_id"] = "case_pay"
    with pytest.raises(jsonschema.exceptions.ValidationError):
        jsonschema.validate(instance=invalid_data, schema=public_schema)

    with open('benchmark/schemas/ground_truth.json') as f:
        ground_truth_schema = json.load(f)
    with open('benchmark/schemas/output_contract.json') as f:
        output_schema = json.load(f)
    expected_vocabulary = HOLD_FINDINGS | INVESTIGATE_FINDINGS
    assert set(ground_truth_schema["properties"]["expected_findings"]["items"]["enum"]) == expected_vocabulary
    assert set(output_schema["properties"]["findings"]["items"]["enum"]) == expected_vocabulary
