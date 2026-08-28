import json
import time
import os
from datetime import datetime
from typing import Any, Dict

class TraceLogger:
    def __init__(self, log_dir: str = "traces"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        # Create a new run trace file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"trace_{timestamp}.jsonl")
    
    def log_event(self, phase: str, agent: str, action: str, tool: str, input_data: Any, output_data: Any, result: str, error: str = None, latency_ms: int = 0):
        """
        Log an agent interaction event into the trace.
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phase": phase,
            "agent": agent,
            "action": action,
            "tool": tool,
            "input": input_data,
            "output": output_data,
            "result": result,
            "error": error,
            "latency_ms": latency_ms
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        # Also print to terminal if it's an error
        if result == "ERROR":
            print(f"[TRACE ERROR] Phase: {phase} | Agent: {agent} | Action: {action} | Error: {error}")
