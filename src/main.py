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
    load_dotenv(dotenv_path=os.environ.get("TOKENROUTER_ENV_FILE", ".env"), override=False)
    load_dotenv(dotenv_path=os.environ.get("NVIDIA_ENV_FILE", "nvidia.local.env"), override=False)
    parser = argparse.ArgumentParser(description="micro1 Hackathon Agent Scaffold")
    parser.add_argument("--smoke", action="store_true", help="Run a smoke test")
    parser.add_argument("--run-all", action="store_true", help="Run the agent on all public cases")
    parser.add_argument("--file", type=str, help="Path to a specific AP evidence bundle JSON file for processing")
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
    elif args.file:
        if not os.path.exists(args.file):
            print(f"ERROR: File not found: {args.file}")
            return
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY environment variable is not set.")
            return
            
        orchestrator = AgentOrchestrator(api_key=api_key)
        case_id = os.path.basename(args.file).replace(".json", "")
        
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                raw_evidence = f.read()
        except Exception as e:
            print(f"ERROR: Failed to read file {args.file}: {e}")
            return
            
        print(f"Processing evidence bundle: {args.file}...\n")
        try:
            result = orchestrator.run_workflow(case_id, raw_evidence)
            
            print("============================================================")
            print("AP EVIDENCE BUNDLE REVIEW")
            print("============================================================")
            
            print("\n[1] CASE SUMMARY")
            print(f"  Target Bundle: {args.file}")
            print(f"  Case ID:       {case_id}")
            print(f"  Result:        {result.get('recommendation', 'UNKNOWN')}")
            
            print("\n[2] EXTRACTED FACTS")
            if hasattr(orchestrator, 'last_extracted_data') and orchestrator.last_extracted_data:
                ex_data = orchestrator.last_extracted_data
                print("  Vendor:")
                vendor = ex_data.get('vendor_master', {})
                if vendor:
                    print(f"    Name: {vendor.get('vendor_name', 'N/A')}")
                    print(f"    Tax ID: {vendor.get('vendor_tax_id', 'N/A')}")
                    print(f"    Bank: {vendor.get('bank_account', 'N/A')}")
                else:
                    print("    (Missing or Unextracted)")
                
                print("  Invoice:")
                invoice = ex_data.get('invoice', {})
                if invoice:
                    print(f"    Inv #: {invoice.get('invoice_number', 'N/A')}")
                    print(f"    Amount: {invoice.get('total', 'N/A')} {invoice.get('currency', 'N/A')}")
                else:
                    print("    (Missing or Unextracted)")
            else:
                print("  (No extracted facts available)")
                
            print("\n[3] FINDINGS & EVIDENCE")
            if "findings" in result and result["findings"]:
                for finding in result["findings"]:
                    print(f"  - {finding}")
            else:
                print("  - None")

            if "evidence_references" in result and result["evidence_references"]:
                print("  Evidence Linked:")
                if isinstance(result["evidence_references"], list):
                    for item in result["evidence_references"]:
                        print(f"    - {item}")
                elif isinstance(result["evidence_references"], dict):
                    for key, value in result["evidence_references"].items():
                        print(f"    - {key}: {value}")
                else:
                    print(f"    {result['evidence_references']}")
                    
            if "missing_evidence" in result and result["missing_evidence"]:
                print("  Missing Evidence:")
                if isinstance(result["missing_evidence"], list):
                    for item in result["missing_evidence"]:
                        print(f"    - {item}")
                else:
                    print(f"    {result['missing_evidence']}")
                
            if "deterministic_calculation_references" in result and result["deterministic_calculation_references"]:
                print("  Calculations Executed:")
                if isinstance(result["deterministic_calculation_references"], list):
                    for item in result["deterministic_calculation_references"]:
                        print(f"    - {item}")
                elif isinstance(result["deterministic_calculation_references"], dict):
                    for key, value in result["deterministic_calculation_references"].items():
                        print(f"    - {key}: {value}")
                else:
                    print(f"    {result['deterministic_calculation_references']}")
                    
            if "required_human_next_step" in result:
                print(f"  Human Next Step: {result['required_human_next_step']}")

            print("\n[4] AUDIT TRACE REFERENCE")
            if hasattr(orchestrator, 'logger') and hasattr(orchestrator.logger, 'log_file'):
                print(f"  Trace File: {orchestrator.logger.log_file}")
            else:
                print("  Trace File: (Not found)")

            print("\n[5] DEMO MODE: ACTION")
            recommendation = result.get('recommendation', 'UNKNOWN')
            if recommendation == "PAY":
                print("  => Proceeding with automated clearing. No human approval required.")
            elif recommendation == "HOLD":
                print("  => Automated clearing stopped. Escalating to human for anomaly review.")
            elif recommendation == "INVESTIGATE":
                print("  => Severe failure or lack of evidence. Full human investigation required.")
            else:
                print(f"  => UNKNOWN STATE: {recommendation}")

            print("============================================================")
            
        except Exception as e:
            print(f"ERROR: Agent orchestration failed: {e}")
            
    else:
        print("Please specify a command. For now, try: python -m src.main --smoke, --run-all, or --file <path>")

if __name__ == "__main__":
    main()
