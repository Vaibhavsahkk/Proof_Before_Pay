import pytest
import sys
from unittest.mock import patch, MagicMock
from src.utils.human_checkpoint import request_human_approval
from src.utils.logger import TraceLogger

def test_approval_granted():
    with patch("builtins.input", return_value="y"), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval("test", "test", "test", "test", "test")
        assert result is True

def test_approval_denied():
    with patch("builtins.input", return_value="n"), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval("test", "test", "test", "test", "test")
        assert result is False

def test_invalid_approval_responses():
    # It should ask again until valid. We mock it to give invalid then valid
    with patch("builtins.input", side_effect=["invalid", "maybe", "y"]), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval("test", "test", "test", "test", "test")
        assert result is True

def test_eof_non_interactive_execution():
    with patch("sys.stdin.isatty", return_value=False):
        result = request_human_approval("test", "test", "test", "test", "test")
        assert result is False

def test_eof_error():
    with patch("builtins.input", side_effect=EOFError), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval("test", "test", "test", "test", "test")
        assert result is False

def test_approval_audit_logging():
    mock_logger = MagicMock(spec=TraceLogger)
    with patch("builtins.input", return_value="y"), patch("sys.stdin.isatty", return_value=True):
        request_human_approval("action1", "reason1", "risk1", "result1", "cons1", logger=mock_logger)
        
    mock_logger.log_event.assert_called_once()
    call_args = mock_logger.log_event.call_args[1]
    assert call_args["agent"] == "human_checkpoint"
    assert call_args["input_data"]["action_requested"] == "action1"
    assert call_args["output_data"]["decision"] == "APPROVED"
