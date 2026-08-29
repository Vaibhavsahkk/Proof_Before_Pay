import pytest
import os
import json
from decimal import Decimal

# Test the Phase 1 validation assertions themselves (positive and negative/adversarial cases).

def test_leakage_validator_fails_on_leakage(tmp_path):
    from scripts.validate_phase1 import test_leakage
    
    # Create fake leaked public file
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    
    with open(cases_dir / "case_leak.json", "w") as f:
        f.write('{"invoice_number": "INV-1001", "expected_recommendation": "PAY"}')
        
    # Patch glob in the script to look at tmp_path
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

def test_arithmetic_validator_fails_on_bad_math(tmp_path):
    from scripts.validate_phase1 import validate_arithmetic
    
    cases_dir = tmp_path / "data" / "cases" / "public"
    cases_dir.mkdir(parents=True)
    
    bad_data = {
        "invoice": {
            "items": [{"quantity": "2", "unit_price": "2.00", "line_total": "5.00"}],
            "subtotal": "4.00",
            "tax": "0.00",
            "total": "4.00"
        }
    }
    with open(cases_dir / "case_bad_math.json", "w") as f:
        json.dump(bad_data, f)
        
    import glob
    original_glob = glob.glob
    def mock_glob(pattern):
        if pattern == 'data/cases/public/*.json':
            return [str(cases_dir / "case_bad_math.json")]
        return []
        
    try:
        import scripts.validate_phase1
        scripts.validate_phase1.glob.glob = mock_glob
        with pytest.raises(AssertionError) as exc:
            validate_arithmetic()
        assert "Line total mismatch" in str(exc.value)
    finally:
        scripts.validate_phase1.glob.glob = original_glob
