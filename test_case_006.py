import os
import json
from dotenv import load_dotenv

from src.agent.orchestrator import AgentOrchestrator
from src.agent.credentials import CredentialManager

def main():
    load_dotenv()
    
    cred_manager = CredentialManager()
    
    orchestrator = AgentOrchestrator(credential_manager=cred_manager)
    
    case_id = "case_006"
    input_file = f"data/cases/public/{case_id}.json"
    
    print(f"Running agent on {case_id}...")
    
    with open(input_file, "r") as f:
        raw_evidence = f.read()
        
    try:
        result = orchestrator.run_workflow(case_id, raw_evidence)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error on {case_id}: {e}")

if __name__ == "__main__":
    main()
