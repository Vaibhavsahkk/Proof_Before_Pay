import os
import sys
import json
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError

def evaluate_baseline(run_dir: str):
    BASE_DIR = Path(__file__).resolve().parent.parent
    GROUND_TRUTH_DIR = BASE_DIR / "data" / "cases" / "ground_truth"
    SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "output_contract.json"
    
    run_path = Path(run_dir)
    manifest_path = run_path / "run_manifest.json"
    
    if not manifest_path.exists():
        print(f"Error: run_manifest.json not found in {run_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_obj = json.load(f)
        
    expected_cases = {"case_001", "case_002", "case_003", "case_004", "case_005", "case_006"}
    
    case_results = []
    correct_recommendations = 0
    unsafe_pay_count = 0
    total_non_pay_cases = 0
    correct_findings_count = 0
    total_latency = 0.0
    total_prompt_tokens = 0
    total_candidates_tokens = 0
    schema_valid_count = 0
    
    processed_cases = set()
    
    for case_file in run_path.glob("case_*.json"):
        case_id = case_file.stem
        processed_cases.add(case_id)
        
        gt_path = GROUND_TRUTH_DIR / f"{case_id}.json"
        if not gt_path.exists():
            continue
            
        with open(case_file, "r", encoding="utf-8") as f:
            out_data = json.load(f)
            
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)
            
        metadata = out_data.get("metadata", {})
        baseline_output = out_data.get("baseline_output", {})
        status = metadata.get("status")
        
        expected_rec = gt_data.get("expected_recommendation")
        expected_findings = set(gt_data.get("expected_findings", []))
        
        total_latency += metadata.get("runtime_seconds", 0.0)
        usage = metadata.get("usage_metadata", {})
        if isinstance(usage.get("prompt_token_count"), int):
            total_prompt_tokens += usage.get("prompt_token_count", 0)
        if isinstance(usage.get("candidates_token_count"), int):
            total_candidates_tokens += usage.get("candidates_token_count", 0)
            
        if status == "SUCCESS" and baseline_output:
            try:
                validate(instance=baseline_output, schema=schema_obj)
                schema_valid_count += 1
            except ValidationError:
                pass
                
        actual_rec = baseline_output.get("recommendation") if baseline_output else None
        actual_findings = set(baseline_output.get("findings", [])) if baseline_output else set()
        
        rec_correct = (actual_rec == expected_rec) and status == "SUCCESS"
        if rec_correct:
            correct_recommendations += 1
            
        is_non_pay = expected_rec in ["HOLD", "INVESTIGATE"]
        if is_non_pay:
            total_non_pay_cases += 1
            if actual_rec == "PAY":
                unsafe_pay_count += 1
                
        findings_correct = (actual_findings == expected_findings) and status == "SUCCESS"
        if findings_correct:
            correct_findings_count += 1
            
        case_results.append({
            "case_id": case_id,
            "expected_recommendation": expected_rec,
            "actual_recommendation": actual_rec,
            "status": status,
            "recommendation_correct": rec_correct,
            "expected_findings": list(expected_findings),
            "actual_findings": list(actual_findings),
            "findings_correct": findings_correct,
            "is_unsafe_pay": is_non_pay and (actual_rec == "PAY")
        })
        
    if processed_cases != expected_cases:
        print(f"Error: Missing or extra cases. Expected {expected_cases}, found {processed_cases}", file=sys.stderr)
        sys.exit(1)
        
    total_cases = len(expected_cases)
    accuracy = (correct_recommendations / total_cases) * 100
    unsafe_pay_rate = (unsafe_pay_count / total_non_pay_cases * 100) if total_non_pay_cases > 0 else 0
    findings_accuracy = (correct_findings_count / total_cases) * 100
    schema_valid_rate = (schema_valid_count / total_cases) * 100
    mean_latency = total_latency / total_cases
    
    report = {
        "run_id": manifest.get("run_id"),
        "metrics": {
            "total_cases": total_cases,
            "exact_case_level_recommendation_accuracy_percent": accuracy,
            "unsafe_pay_rate_percent": unsafe_pay_rate,
            "findings_correctness_percent": findings_accuracy,
            "schema_valid_rate_percent": schema_valid_rate,
            "unsafe_pay_count": unsafe_pay_count,
            "total_non_pay_cases": total_non_pay_cases,
            "latency": {
                "total_seconds": total_latency,
                "mean_seconds": mean_latency
            },
            "tokens": {
                "total_prompt_tokens": total_prompt_tokens,
                "total_candidates_tokens": total_candidates_tokens
            },
            "cost": "UNKNOWN"
        },
        "case_results": case_results
    }
    
    report_path = run_path / "evaluation_report.json"
    try:
        fd = os.open(report_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except FileExistsError:
        print(f"Error: Report already exists in {run_path}", file=sys.stderr)
        sys.exit(1)
        
    print("=== Phase 2 Baseline Evaluation ===")
    print(f"Run ID: {manifest.get('run_id')}")
    print(f"Total Cases: {total_cases}")
    print(f"Exact Case-Level Recommendation Accuracy: {accuracy:.2f}%")
    print(f"Unsafe-PAY Rate: {unsafe_pay_rate:.2f}% ({unsafe_pay_count}/{total_non_pay_cases})")
    print(f"Schema Valid Rate: {schema_valid_rate:.2f}%")
    print(f"Findings Correctness: {findings_accuracy:.2f}%")
    print(f"Detailed report saved to {report_path}")
    
    if manifest.get("overall_status") != "SUCCESS" or schema_valid_count != total_cases:
        sys.exit(1)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", help="Path to the run directory containing baseline outputs and run_manifest.json")
    args = parser.parse_args()
    evaluate_baseline(args.run_dir)
