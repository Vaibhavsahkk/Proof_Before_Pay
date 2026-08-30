import pytest
import os
from unittest.mock import MagicMock, patch
from src.agent.orchestrator import AgentOrchestrator

@pytest.fixture
def mock_extractor():
    with patch("src.agent.orchestrator.LLMExtractor") as MockClass:
        mock_instance = MockClass.return_value
        mock_instance.extract_evidence.return_value = {
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
        mock_instance.generate_explanation.return_value = ("No uncertainty", "Approve payment")
        yield mock_instance

def test_agent_orchestrator_pay_flow(mock_extractor):
    orchestrator = AgentOrchestrator(api_key="fake")
    result = orchestrator.run_workflow("case_001", "fake raw evidence")
    
    assert result["recommendation"] == "PAY"
    assert result["findings"] == []
    assert result["case_id"] == "case_001"

def test_agent_orchestrator_investigate_flow(mock_extractor):
    # Alter mock to cause an INVESTIGATE finding: Vendor Name Mismatch
    mock_extractor.extract_evidence.return_value["invoice"]["vendor_name"] = "Mismatch Vendor"
    
    orchestrator = AgentOrchestrator(api_key="fake")
    result = orchestrator.run_workflow("case_002", "fake raw evidence")
    
    assert result["recommendation"] == "INVESTIGATE"
    assert "Vendor Identity Mismatch" in result["findings"]

def test_agent_orchestrator_hold_flow(mock_extractor):
    # Alter mock to cause a HOLD finding: Math Error (wrong line total)
    mock_extractor.extract_evidence.return_value["invoice"]["items"][0]["line_total"] = "99.00"
    
    orchestrator = AgentOrchestrator(api_key="fake")
    result = orchestrator.run_workflow("case_003", "fake raw evidence")
    
    assert result["recommendation"] == "HOLD"
    assert "Math Error" in result["findings"]

def test_agent_orchestrator_fail_closed_on_error(mock_extractor):
    with patch("src.agent.orchestrator.RuleEvaluator.evaluate", side_effect=Exception("Simulated error")):
        orchestrator = AgentOrchestrator(api_key="fake")
        result = orchestrator.run_workflow("case_004", "fake raw evidence")
        
        assert result["recommendation"] == "INVESTIGATE"
        assert "Extraction or System Failure" in result["findings"]
