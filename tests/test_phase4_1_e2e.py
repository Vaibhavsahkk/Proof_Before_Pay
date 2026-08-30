import pytest
import subprocess
import json
import os
import sys

def test_cli_smoke():
    """Test that the CLI smoke command works."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--smoke"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Running smoke test..." in result.stdout
    assert "Smoke test complete" in result.stdout

def test_cli_file_processing():
    """Test that the CLI processes a valid evidence bundle file and outputs formatted text."""
    case_file = "data/cases/public/case_001.json"
    if not os.path.exists(case_file):
        pytest.skip("Test case file not found")
        
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--file", case_file],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Processing evidence bundle: data/cases/public/case_001.json..." in result.stdout
    assert "Result:        PAY" in result.stdout
    assert "  - None" in result.stdout
    assert "  Evidence Linked:" in result.stdout
    assert "  Calculations Executed:" in result.stdout
    assert "  Human Next Step: A human reviewer must make the final decision to approve the PAY recommendation." in result.stdout

from src.agent.orchestrator import AgentOrchestrator
from unittest.mock import patch

def test_malformed_input_system_failure():
    """Test that malformed input or system failure is caught and safely defaults to INVESTIGATE."""
    orchestrator = AgentOrchestrator(api_key="dummy")
    
    with patch.object(orchestrator, 'extractor') as mock_extractor:
        mock_extractor.extract_evidence.side_effect = Exception("Simulated fatal error")
        
        result = orchestrator.run_workflow("test_case", "invalid input data")
        
        assert result["recommendation"] == "INVESTIGATE"
        assert "Extraction or System Failure" in result["findings"]
        assert "System failure occurred" in result["uncertainty"]

def test_hold_flow():
    """Test that a case resulting in HOLD is properly processed via CLI."""
    case_file = "data/cases/public/case_002.json" # Case 002 is HOLD (Duplicate Billing)
    if not os.path.exists(case_file):
        pytest.skip("Test case file not found")
        
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--file", case_file],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Result:        HOLD" in result.stdout
    assert "Duplicate Billing" in result.stdout
    assert "  Human Next Step:" in result.stdout

def test_missing_evidence_flow():
    """Test that a case with missing evidence results in INVESTIGATE."""
    case_file = "data/cases/public/case_011.json" # Case 11 has Missing Vendor Master
    if not os.path.exists(case_file):
        pytest.skip("Test case file not found")
        
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--file", case_file],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Result:        INVESTIGATE" in result.stdout
    assert "Missing Vendor Master" in result.stdout
    assert "  Missing Evidence:" in result.stdout
