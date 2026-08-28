import json
import os
import uuid
import re
from datetime import datetime
from typing import Any, Dict

class TraceLogger:
    def __init__(self, log_dir: str = "traces"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        # Collision-resistant filename
        self.run_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"trace_{timestamp}_{self.run_id[:8]}.jsonl")

    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize secrets and ensure JSON serializability."""
        # Handle non-serializable objects by converting to string
        try:
            # Test if it's purely serializable
            json.dumps(data)
            safe_data = data
        except (TypeError, ValueError):
            safe_data = str(data)
            
        json_str = json.dumps(safe_data)
        
        # Redact secrets
        # Match typical API keys like sk-...
        json_str = re.sub(r'sk-[a-zA-Z0-9]{20,}', '***REDACTED***', json_str)
        # Match Anthropic keys
        json_str = re.sub(r'sk-ant-[a-zA-Z0-9_-]{20,}', '***REDACTED***', json_str)
        # Match Bearer tokens
        json_str = re.sub(r'Bearer\s+[a-zA-Z0-9\-\._~+/]+', 'Bearer ***REDACTED***', json_str)
        
        return json.loads(json_str)

    def log_event(self, phase: str, agent: str, action: str, tool: str, input_data: Any, output_data: Any, result: str, error: str = None, latency_ms: int = 0):
        """
        Log an agent interaction event into the trace.
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "phase": phase,
            "agent": agent,
            "action": action,
            "tool": tool,
            "input": self._sanitize_data(input_data),
            "output": self._sanitize_data(output_data),
            "result": result,
            "error": str(error) if error else None,
            "latency_ms": latency_ms
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        
        if result == "ERROR":
            print(f"[TRACE ERROR] Phase: {phase} | Agent: {agent} | Action: {action} | Error: {error}")
