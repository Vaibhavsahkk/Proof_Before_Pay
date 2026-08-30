import argparse
import os
import glob
import json
import time
from dotenv import load_dotenv
from src.utils.logger import TraceLogger
from src.utils.human_checkpoint import request_human_approval
from src.agent.orchestrator import AgentOrchestrator

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="micro1 Hackathon Agent Scaffold")
    parser.add_argument("--smoke", action="store_true", help="Run a smoke test")
    parser.add_argument("--run-all", action="store_true", help="Run the agent on all public cases")
    args = parser.parse_args()

    if args.smoke:
        print("Running smoke test...")
        logger = TraceLogger()
        logger.log_event(
            phase="smoke_test",
            agent="system",
            action="init",
            tool="none",
            input_data={"status": "starting"},
            output_data={"status": "success"},
            result="SUCCESS"
        )
        print("Smoke test complete. Check traces directory for output.")
    elif args.run_all:
        print("Running agent on all public cases...")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable is not set.")
            return
            
        orchestrator = AgentOrchestrator(api_key=api_key)
        results = {}
        
        case_files = sorted(glob.glob("data/cases/public/case_*.json"))
        for i, case_file in enumerate(case_files):
            case_id = os.path.basename(case_file).replace(".json", "")
            print(f"\nProcessing {case_id}...")
            with open(case_file, "r", encoding="utf-8") as f:
                raw_evidence = f.read()
            
            result = orchestrator.run_workflow(case_id, raw_evidence)
            results[case_id] = result
            print(f"Result for {case_id}: {result['recommendation']} - {result['findings']}")
            if i < len(case_files) - 1:
                pass
            
        os.makedirs("reports", exist_ok=True)
        with open("reports/phase_3_3_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print("\nResults saved to reports/phase_3_3_results.json")
    else:
        print("Please specify a command. For now, try: python -m src.main --smoke or --run-all")

if __name__ == "__main__":
    main()
