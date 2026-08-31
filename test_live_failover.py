import os
from dotenv import load_dotenv
from src.agent.orchestrator import AgentOrchestrator

load_dotenv()
keys = os.environ.get("GEMINI_API_KEYS")
orchestrator = AgentOrchestrator(api_key=keys)

with open("data/cases/public/case_001.json", "r", encoding="utf-8") as f:
    raw_evidence = f.read()

print("Processing case_001...")
result = orchestrator.run_workflow("case_001", raw_evidence)
print("Result:", result.get("recommendation"))
