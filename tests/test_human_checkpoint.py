import pytest
from unittest.mock import patch, MagicMock
from src.utils.human_checkpoint import request_human_approval
from src.utils.logger import TraceLogger, TraceLoggerError

def test_approval_granted_with_mandatory_audit_log(tmp_path):
    mock_logger = MagicMock(spec=TraceLogger)
    with patch("builtins.input", return_value="y"), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval(
            action="deploy_agent",
            reason="testing",
            risk="low",
            expected_result="agent deployed",
            consequence_if_declined="nothing",
            logger=mock_logger,
            phase="phase_0"
        )
        assert result is True
        mock_logger.log_event.assert_called_once()
        call_kwargs = mock_logger.log_event.call_args[1]
        assert call_kwargs["phase"] == "phase_0"
        assert call_kwargs["agent"] == "human_checkpoint"
        assert call_kwargs["output_data"]["decision"] == "APPROVED"
        assert call_kwargs["result"] == "SUCCESS"

def test_approval_denied_with_audit_log():
    mock_logger = MagicMock(spec=TraceLogger)
    with patch("builtins.input", return_value="n"), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval(
            action="destructive_action",
            reason="test_denial",
            risk="high",
            expected_result="data deleted",
            consequence_if_declined="safe",
            logger=mock_logger
        )
        assert result is False
        mock_logger.log_event.assert_called_once()
        call_kwargs = mock_logger.log_event.call_args[1]
        assert call_kwargs["output_data"]["decision"] == "DECLINED"
        assert call_kwargs["result"] == "DECLINED"

def test_eof_error_fails_closed_with_audit_log():
    mock_logger = MagicMock(spec=TraceLogger)
    with patch("builtins.input", side_effect=EOFError), patch("sys.stdin.isatty", return_value=True):
        result = request_human_approval(
            action="action",
            reason="reason",
            risk="risk",
            expected_result="result",
            consequence_if_declined="decline",
            logger=mock_logger
        )
        assert result is False
        mock_logger.log_event.assert_called_once()
        call_kwargs = mock_logger.log_event.call_args[1]
        assert call_kwargs["output_data"]["decision"] == "DECLINED"

def test_non_interactive_mode_fails_closed():
    mock_logger = MagicMock(spec=TraceLogger)
    with patch("sys.stdin.isatty", return_value=False):
        result = request_human_approval(
            action="action",
            reason="reason",
            risk="risk",
            expected_result="result",
            consequence_if_declined="decline",
            logger=mock_logger
        )
        assert result is False
        mock_logger.log_event.assert_called_once()
        call_kwargs = mock_logger.log_event.call_args[1]
        assert call_kwargs["output_data"]["decision"] == "DECLINED"

def test_audit_write_failure_fails_closed():
    mock_logger = MagicMock(spec=TraceLogger)
    mock_logger.log_event.side_effect = TraceLoggerError("Disk write failed")

    with patch("builtins.input", return_value="y"), patch("sys.stdin.isatty", return_value=True):
        # Human approves ('y'), BUT audit log write fails -> MUST FAIL CLOSED (return False)!
        result = request_human_approval(
            action="critical_action",
            reason="testing audit failure",
            risk="extreme",
            expected_result="system updated",
            consequence_if_declined="aborted",
            logger=mock_logger
        )
        assert result is False
