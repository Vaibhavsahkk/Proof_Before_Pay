import os
import json
import pytest
from src.utils.logger import TraceLogger

@pytest.fixture
def logger(tmp_path):
    return TraceLogger(log_dir=str(tmp_path))

def test_normal_trace_logging(logger):
    logger.log_event(
        phase="test",
        agent="agent1",
        action="action1",
        tool="tool1",
        input_data={"key": "value"},
        output_data={"result": "success"},
        result="SUCCESS"
    )
    assert os.path.exists(logger.log_file)
    with open(logger.log_file, "r") as f:
        data = json.loads(f.readline())
        assert data["phase"] == "test"
        assert data["input"]["key"] == "value"

def test_malformed_non_json_values(logger):
    class Unserializable:
        pass
    
    logger.log_event(
        phase="test",
        agent="agent1",
        action="action1",
        tool="tool1",
        input_data=Unserializable(),
        output_data={"result": "success"},
        result="SUCCESS"
    )
    with open(logger.log_file, "r") as f:
        data = json.loads(f.readline())
        assert "Unserializable" in str(data["input"])

def test_unicode_logging(logger):
    logger.log_event(
        phase="test",
        agent="agent1",
        action="action1",
        tool="tool1",
        input_data={"key": "こんにちは"},
        output_data={"result": "success"},
        result="SUCCESS"
    )
    with open(logger.log_file, "r", encoding="utf-8") as f:
        data = json.loads(f.readline())
        assert data["input"]["key"] == "こんにちは"

def test_secret_redaction(logger):
    secrets = {
        "api_key": "sk-12345678901234567890",
        "anthropic_key": "sk-ant-api03-12345678901234567890",
        "token": "Bearer abcdefg12345"
    }
    logger.log_event(
        phase="test",
        agent="agent1",
        action="action1",
        tool="tool1",
        input_data=secrets,
        output_data={"result": "success"},
        result="SUCCESS"
    )
    with open(logger.log_file, "r") as f:
        data = json.loads(f.readline())
        assert "sk-123" not in str(data["input"])
        assert "sk-ant" not in str(data["input"])
        assert "abcdefg" not in str(data["input"])
        assert "***REDACTED***" in str(data["input"])
