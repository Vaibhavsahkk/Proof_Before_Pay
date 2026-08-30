import json
import os
import glob

def main():
    with open("reports/phase_3_5_results.json", "r") as f:
        results = json.load(f)

    gt_files = sorted(glob.glob("data/cases/ground_truth/case_*.json"))
    
    total_cases = len(gt_files)
    correct_recommendations = 0
    correct_findings = 0
    unsafe_pay_count = 0
    total_non_pay = 0
    
    for gt_file in gt_files:
        case_id = os.path.basename(gt_file).replace(".json", "")
        with open(gt_file, "r") as f:
            gt = json.load(f)
            
        expected_rec = gt["expected_recommendation"]
        expected_findings = set(gt["expected_findings"])
        
        actual = results.get(case_id, {})
        actual_rec = actual.get("recommendation", "ERROR")
        actual_findings = set(actual.get("findings", []))
        
        if actual_rec == expected_rec:
            correct_recommendations += 1
            
        if actual_findings == expected_findings:
            correct_findings += 1
            
        is_non_pay = expected_rec in {"HOLD", "INVESTIGATE"}
        if is_non_pay:
            total_non_pay += 1
            if actual_rec == "PAY":
                unsafe_pay_count += 1

    report = {
        "metrics": {
            "total_cases": total_cases,
            "exact_case_level_recommendation_accuracy_percent": (correct_recommendations / total_cases) * 100,
            "findings_correctness_percent": (correct_findings / total_cases) * 100,
            "unsafe_pay_rate_percent": (unsafe_pay_count / total_non_pay) * 100 if total_non_pay > 0 else 0,
            "unsafe_pay_count": unsafe_pay_count,
            "total_non_pay_cases": total_non_pay
        }
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/phase_3_5_evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Phase 3.5 Evaluation Metrics:")
    print(json.dumps(report["metrics"], indent=2))

if __name__ == "__main__":
    main()
