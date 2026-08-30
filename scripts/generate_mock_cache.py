import os
import glob
import json
from src.tools.rule_evaluator import RuleEvaluator
from src.agent.orchestrator import AgentOrchestrator

def main():
    os.makedirs("data/cache/extractions", exist_ok=True)
    os.makedirs("data/cache/explanations", exist_ok=True)
    
    # We need a dummy orchestrator just to use the deterministic checks
    # and rule evaluator to get the findings for the explanations.
    orchestrator = AgentOrchestrator(api_key="mock")
    
    case_files = glob.glob("data/cases/public/case_*.json")
    for case_file in case_files:
        case_id = os.path.basename(case_file).replace(".json", "")
        print(f"Mocking cache for {case_id}...")
        
        # 1. Extraction is just parsing the JSON file
        with open(case_file, "r", encoding="utf-8") as f:
            raw_evidence_str = f.read()
            extracted_data = json.loads(raw_evidence_str)
            
        with open(f"data/cache/extractions/{case_id}.json", "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, indent=2)
            
        # 2. Get findings to mock the explanation
        anomalies = orchestrator._run_deterministic_verification(extracted_data)
        rule_result = RuleEvaluator.evaluate(anomalies)
        findings = rule_result["findings"]
        
        # Create a deterministic, mocked explanation based on findings
        if not findings:
            uncertainty = "No material uncertainty identified."
            next_step = "A human reviewer must make the final decision to approve the PAY recommendation."
        else:
            uncertainty = f"System identified {len(findings)} anomalies: {', '.join(findings)}"
            next_step = "Human investigation required to clear anomalies before payment."
            
        with open(f"data/cache/explanations/{case_id}.json", "w", encoding="utf-8") as f:
            json.dump({
                "uncertainty": uncertainty,
                "required_human_next_step": next_step
            }, f, indent=2)
            
    print("Mock cache generation complete.")

if __name__ == "__main__":
    main()
