import os
import json
import glob
from dotenv import load_dotenv

from src.agent.orchestrator import AgentOrchestrator

def main():
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment.")
    
    orchestrator = AgentOrchestrator(api_key=api_key)
    
    input_files = sorted(glob.glob("data/cases/public/case_*.json"))
    results = {}
    
    for input_file in input_files:
        case_id = os.path.basename(input_file).replace(".json", "")
        print(f"Running agent on {case_id}...")
        
        with open(input_file, "r") as f:
            raw_evidence = f.read()
            
        try:
            result = orchestrator.run_workflow(case_id, raw_evidence)
            results[case_id] = result
        except Exception as e:
            print(f"Error on {case_id}: {e}")
            results[case_id] = {"error": str(e)}
            
    os.makedirs("reports", exist_ok=True)
    with open("reports/phase_3_7_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Done. Saved to reports/phase_3_7_results.json")

if __name__ == "__main__":
    main()
