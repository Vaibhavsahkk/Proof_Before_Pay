import json
import os
import uuid
import re
from datetime import datetime, timezone
from typing import Any, Dict, Union

class TraceLoggerError(RuntimeError):
    """Exception raised when trace logger fails to write or initialize."""
    pass

class TraceLogger:
    SENSITIVE_KEYS = {
        "api_key", "apikey", "secret", "token", "password", "auth", 
        "authorization", "private_key", "credentials", "access_token", 
        "refresh_token", "secret_key"
    }

    SECRET_PATTERNS = [
        re.compile(r'sk-proj-[a-zA-Z0-9_\-\.]+'),
        re.compile(r'sk-ant-[a-zA-Z0-9_\-\.]+'),
        re.compile(r'sk-[a-zA-Z0-9_\-\.]{20,}'),
        re.compile(r'Bearer\s+[a-zA-Z0-9\-\._~+/]+=*', re.IGNORECASE),
        re.compile(r'ghp_[a-zA-Z0-9]{36}'),
        re.compile(r'AKIA[0-9A-Z]{16}'),
    ]

    def __init__(self, log_dir: str = "traces/raw"):
        self.log_dir = log_dir
        try:
            os.makedirs(self.log_dir, exist_ok=True)
        except Exception as e:
            raise TraceLoggerError(f"Failed to create trace directory '{log_dir}': {e}") from e

        self.run_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"trace_{timestamp}_{self.run_id[:8]}.jsonl")

    SAFE_TELEMETRY_KEYS = {
        "prompt_tokens", "completion_tokens", "total_tokens", "latency", "cost", "latency_ms"
    }

    @classmethod
    def sanitize_value(cls, val: Any, key_name: str = "") -> Any:
        """Recursively sanitize dicts, lists, strings, and arbitrary objects."""
        if isinstance(val, dict):
            sanitized_dict = {}
            for k, v in val.items():
                str_key = str(k)
                if str_key.lower() in cls.SAFE_TELEMETRY_KEYS:
                    # Enforce that telemetry values are strictly non-negative numbers
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0:
                        sanitized_dict[str_key] = v
                    else:
                        sanitized_dict[str_key] = "***REDACTED***"
                elif any(sens in str_key.lower() for sens in cls.SENSITIVE_KEYS):
                    sanitized_dict[str_key] = "***REDACTED***"
                else:
                    sanitized_dict[str_key] = cls.sanitize_value(v, str_key)
            return sanitized_dict
        elif isinstance(val, (list, tuple, set)):
            return [cls.sanitize_value(item, key_name) for item in val]
        elif isinstance(val, str):
            res = val
            for pattern in cls.SECRET_PATTERNS:
                res = pattern.sub('***REDACTED***', res)
            return res
        elif isinstance(val, (int, float, bool, type(None))):
            return val
        else:
            # Fallback for non-JSON-serializable custom objects
            try:
                # Try json serializable check
                json.dumps(val)
                return val
            except (TypeError, ValueError):
                return cls.sanitize_value(str(val), key_name)

    def log_event(
        self, 
        phase: str, 
        agent: str, 
        action: str, 
        tool: str, 
        input_data: Any, 
        output_data: Any, 
        result: str, 
        error: Any = None, 
        latency_ms: int = 0,
        metadata: Any = None
    ) -> Dict[str, Any]:
        """
        Log an agent interaction event into the trace after full recursive sanitization.
        """
        raw_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "phase": phase,
            "agent": agent,
            "action": action,
            "tool": tool,
            "input": input_data,
            "output": output_data,
            "result": result,
            "error": str(error) if error is not None else None,
            "latency_ms": latency_ms,
            "metadata": metadata
        }

        # Apply recursive sanitization across the entire event dictionary
        sanitized_event = self.sanitize_value(raw_event)

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(sanitized_event) + "\n")
        except Exception as e:
            raise TraceLoggerError(f"Failed to write trace event to '{self.log_file}': {e}") from e

        if result == "ERROR":
            print(f"[TRACE ERROR] Phase: {sanitized_event['phase']} | Agent: {sanitized_event['agent']} | Error: {sanitized_event['error']}")

        return sanitized_event
