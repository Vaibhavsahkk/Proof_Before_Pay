import os
import json
import pytest
from unittest.mock import patch
from src.utils.logger import TraceLogger, TraceLoggerError

@pytest.fixture
def temp_logger(tmp_path):
    return TraceLogger(log_dir=str(tmp_path / "raw"))

def test_normal_trace_logging(temp_logger):
    event = temp_logger.log_event(
        phase="phase_0",
        agent="test_agent",
        action="execute",
        tool="mock_tool",
        input_data={"param": 100},
        output_data={"result": "ok"},
        result="SUCCESS"
    )
    assert os.path.exists(temp_logger.log_file)
    with open(temp_logger.log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["phase"] == "phase_0"
        assert data["agent"] == "test_agent"
        assert data["input"]["param"] == 100

def test_recursive_nested_sanitization_and_sensitive_keys(temp_logger):
    adversarial_payload = {
        "api_key": "my_secret_key_value",
        "nested_dict": {
            "SECRET_TOKEN": "top_secret",
            "normal_field": "hello",
            "deep_list": [
                {"auth_password": "p@ssword123"},
                "sk-proj-999999999999999999999999"
            ]
        },
        "bearer_header": "Bearer secret_jwt_token_here",
        "aws_key": "AKIAIOSFODNN7EXAMPLE",
        "github_token": "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
    }

    event = temp_logger.log_event(
        phase="sk-proj-secretphase123456789000",
        agent="agent_sk-ant-secret123456789000",
        action="sanitize_check",
        tool="tool",
        input_data=adversarial_payload,
        output_data={"token": "should_be_redacted"},
        result="SUCCESS",
        metadata={"private_key": "private_data"}
    )

    with open(temp_logger.log_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())

    # Verify phase sanitization
    assert "sk-proj" not in data["phase"]
    assert "***REDACTED***" in data["phase"]

    # Verify agent sanitization
    assert "sk-ant" not in data["agent"]

    # Verify sensitive key redactions
    assert data["input"]["api_key"] == "***REDACTED***"
    assert data["input"]["nested_dict"]["SECRET_TOKEN"] == "***REDACTED***"
    assert data["input"]["nested_dict"]["deep_list"][0]["auth_password"] == "***REDACTED***"
    assert data["input"]["nested_dict"]["deep_list"][1] == "***REDACTED***"

    # Verify pattern redactions
    assert "secret_jwt" not in data["input"]["bearer_header"]
    assert "AKIAIOSFODNN7EXAMPLE" not in data["input"]["aws_key"]
    assert "ghp_" not in data["input"]["github_token"]

    # Verify metadata redaction
    assert data["metadata"]["private_key"] == "***REDACTED***"

def test_safe_telemetry_preservation(temp_logger):
    event = temp_logger.log_event(
        phase="phase",
        agent="agent",
        action="action",
        tool="tool",
        input_data={"prompt_tokens": 150, "completion_tokens": 50, "latency": 1.2, "cost": 0.005, "some_secret": "hidden"},
        output_data={"prompt_tokens": "sk-proj-malicious123", "cost": -1.5, "latency": True},
        result="SUCCESS"
    )
    with open(temp_logger.log_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())
        
    assert data["input"]["prompt_tokens"] == 150
    assert data["input"]["completion_tokens"] == 50
    assert data["input"]["latency"] == 1.2
    assert data["input"]["cost"] == 0.005
    assert data["input"]["some_secret"] == "***REDACTED***"
    
    # Assert invalid/malicious telemetry types are redacted
    assert data["output"]["prompt_tokens"] == "***REDACTED***"
    assert data["output"]["cost"] == "***REDACTED***"
    assert data["output"]["latency"] == "***REDACTED***"

def test_malformed_unserializable_objects(temp_logger):
    class DummyClass:
        def __str__(self):
            return "DummyObject<sk-proj-secret123456789012345>"

    event = temp_logger.log_event(
        phase="test",
        agent="test",
        action="test",
        tool="test",
        input_data={"obj": DummyClass()},
        output_data=DummyClass(),
        result="SUCCESS"
    )

    with open(temp_logger.log_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())

    assert "sk-proj" not in str(data["input"])
    assert "***REDACTED***" in str(data["input"])

def test_unicode_and_timezone_utc(temp_logger):
    event = temp_logger.log_event(
        phase="test_unicode",
        agent="agent_世界",
        action="action_🚀",
        tool="tool",
        input_data={"msg": "こんにちは"},
        output_data={},
        result="SUCCESS"
    )

    assert "Z" in event["timestamp"] or "+00:00" in event["timestamp"]

    with open(temp_logger.log_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())

    assert data["agent"] == "agent_世界"
    assert data["input"]["msg"] == "こんにちは"

def test_logger_write_failure(tmp_path):
    read_only_dir = tmp_path / "readonly"
    read_only_dir.mkdir()

    logger = TraceLogger(log_dir=str(read_only_dir))

    # Mock open to trigger write failure
    with patch("builtins.open", side_effect=OSError("Permission denied")):
        with pytest.raises(TraceLoggerError) as exc_info:
            logger.log_event(
                phase="test",
                agent="test",
                action="test",
                tool="test",
                input_data={},
                output_data={},
                result="SUCCESS"
            )
        assert "Failed to write trace event" in str(exc_info.value)
