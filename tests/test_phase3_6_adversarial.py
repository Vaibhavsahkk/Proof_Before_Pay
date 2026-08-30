import pytest
import copy
from unittest.mock import patch, MagicMock
from src.agent.orchestrator import AgentOrchestrator
from src.tools.calculator import CalculatorError

# Standard valid extracted data for patching
VALID_EXTRACTED_DATA = {
    "invoice": {
        "vendor_name": "Test Vendor",
        "vendor_tax_id": "123",
        "bank_account": "ACC1",
        "currency": "USD",
        "tax_rate_percent": "0",
        "subtotal": "100.00",
        "tax": "0.00",
        "total": "100.00",
        "items": [
            {"item_id": "L1", "quantity": "10", "unit_price": "10.00", "line_total": "100.00"}
        ]
    },
    "purchase_order": {
        "currency": "USD",
        "tax_rate_percent": "0",
        "items": [
            {"item_id": "L1", "unit_price": "10.00"}
        ]
    },
    "goods_receipt": {
        "items": [
            {"item_id": "L1", "quantity_accepted": "10"}
        ]
    },
    "vendor_master": {
        "vendor_name": "Test Vendor",
        "vendor_tax_id": "123",
        "bank_account": "ACC1"
    }
}

@pytest.fixture
def base_orchestrator():
    orchestrator = AgentOrchestrator(api_key="fake")
    return orchestrator

def _run_with_mock_data(orchestrator, data):
    with patch("src.agent.orchestrator.LLMExtractor.extract_evidence", return_value=data):
        with patch("src.agent.orchestrator.LLMExtractor.generate_explanation", return_value=("None", "Review")):
            return orchestrator.run_workflow("case_000", "fake raw")

def test_A_missing_invoice(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    del data["invoice"]
    # Schema validation might fail or math errors because inv is {}
    res = _run_with_mock_data(base_orchestrator, data)
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]
    assert "PAY" not in res["recommendation"]

def test_B_missing_po(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    del data["purchase_order"]
    res = _run_with_mock_data(base_orchestrator, data)
    assert "Missing PO" in res["missing_evidence"]
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]

def test_C_missing_grn(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    del data["goods_receipt"]
    res = _run_with_mock_data(base_orchestrator, data)
    assert "Missing GRN" in res["missing_evidence"]
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]

def test_D_missing_vendor_master(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    del data["vendor_master"]
    res = _run_with_mock_data(base_orchestrator, data)
    assert "Missing Vendor Master" in res["missing_evidence"]
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]

def test_E_missing_bank_change_evidence(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    # Invoice has different bank account but no bank change evidence
    data["invoice"]["bank_account"] = "ACC2"
    res = _run_with_mock_data(base_orchestrator, data)
    assert "Unverified Bank Change" in res["findings"]
    assert res["recommendation"] == "INVESTIGATE"

def test_F_conflicting_vendor_identity(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    data["invoice"]["vendor_tax_id"] = "999"
    res = _run_with_mock_data(base_orchestrator, data)
    assert "Vendor Identity Mismatch" in res["findings"]
    assert res["recommendation"] == "INVESTIGATE"

def test_G_conflicting_currency(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    data["invoice"]["currency"] = "EUR"
    res = _run_with_mock_data(base_orchestrator, data)
    assert "Invalid Currency" in res["findings"] or "Currency Mismatch" in res["findings"]
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]

def test_H_malformed_extracted_json(base_orchestrator):
    # API returns invalid data structure (e.g. string instead of dict)
    with patch("src.agent.orchestrator.LLMExtractor.extract_evidence", return_value="This is not JSON"):
        res = base_orchestrator.run_workflow("case_000", "fake")
    assert res["recommendation"] == "INVESTIGATE"
    assert "Extraction or System Failure" in res["findings"]

def test_I_missing_required_extraction_field(base_orchestrator):
    # Output schema validator should fail if return structure is fundamentally wrong
    with patch("src.agent.orchestrator.LLMExtractor.extract_evidence", return_value={"random": "data"}):
        with patch("src.agent.orchestrator.LLMExtractor.generate_explanation", return_value=("", "")):
            res = base_orchestrator.run_workflow("case_000", "fake")
    # Schema validation might fail or deterministic logic throws error
    assert res["recommendation"] == "INVESTIGATE"

def test_J_invalid_numeric_value(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    data["invoice"]["items"][0]["quantity"] = "abc"
    res = _run_with_mock_data(base_orchestrator, data)
    # DecimalCalculator should throw CalculatorError, caught and mapped to Math Error
    assert "Math Error" in res["findings"]
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]

def test_K_deterministic_calculator_failure(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    with patch("src.tools.calculator.DecimalCalculator.check_equality", side_effect=Exception("Hard crash")):
        res = _run_with_mock_data(base_orchestrator, data)
    assert res["recommendation"] == "INVESTIGATE"
    assert "Extraction or System Failure" in res["findings"]

def test_L_equality_tool_failure(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    with patch("src.tools.equality.EqualityChecker.is_exact_match", side_effect=Exception("Hard crash")):
        res = _run_with_mock_data(base_orchestrator, data)
    assert res["recommendation"] == "INVESTIGATE"
    assert "Extraction or System Failure" in res["findings"]

def test_M_rule_evaluator_failure(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    with patch("src.tools.rule_evaluator.RuleEvaluator.evaluate", side_effect=Exception("Hard crash")):
        res = _run_with_mock_data(base_orchestrator, data)
    assert res["recommendation"] == "INVESTIGATE"
    assert "Extraction or System Failure" in res["findings"]

def test_N_model_api_unavailable(base_orchestrator):
    with patch("src.agent.orchestrator.LLMExtractor.extract_evidence", side_effect=Exception("503 Service Unavailable")):
        res = base_orchestrator.run_workflow("case_000", "fake")
    assert res["recommendation"] == "INVESTIGATE"
    assert "Extraction or System Failure" in res["findings"]

def test_O_unexpected_tool_response(base_orchestrator):
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    with patch("src.tools.calculator.DecimalCalculator.multiply", return_value=None):
        res = _run_with_mock_data(base_orchestrator, data)
    # Because multiply returns None, check_equality might throw CalculatorError or return False
    assert res["recommendation"] in ["HOLD", "INVESTIGATE"]
    assert "PAY" not in res["recommendation"]

def test_P_unsafe_pay_condition(base_orchestrator):
    # Attempt to bypass deterministic logic: simulate extract_evidence returning perfect data
    # but the rule evaluator is somehow bypassed? No, the rule evaluator is hardcoded.
    # What if explanation step crashes?
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    with patch("src.agent.orchestrator.LLMExtractor.extract_evidence", return_value=data):
        with patch("src.agent.orchestrator.LLMExtractor.generate_explanation", side_effect=Exception("Crash during explanation")):
            res = base_orchestrator.run_workflow("case_000", "fake")
    assert res["recommendation"] == "INVESTIGATE"
    assert "Extraction or System Failure" in res["findings"]

def test_Q_attempted_ground_truth_access(base_orchestrator):
    # Mocking read attempts or just checking that if the agent tried to inject path, it gets sanitized or ignored
    # Orchestrator does not do any file I/O itself except for the schema.
    # We will simulate an extraction that includes a prompt injection to open files.
    data = copy.deepcopy(VALID_EXTRACTED_DATA)
    data["invoice"]["vendor_name"] = "open('data/cases/ground_truth/case_001.json').read()"
    res = _run_with_mock_data(base_orchestrator, data)
    # The deterministic tools will treat it as a literal string and fail the vendor match
    assert "Vendor Identity Mismatch" in res["findings"]
    assert res["recommendation"] == "INVESTIGATE"
