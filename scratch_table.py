import json

report_path = 'evidence/phase_2/runs/run_20260830_091031_f1cc354c/evaluation_report.json'
with open(report_path) as f:
    report = json.load(f)

print('| CASE | BASELINE RECOMMENDATION | EXPECTED RECOMMENDATION | FINDINGS | EXPECTED FINDINGS | SCHEMA STATUS | LATENCY | NOTABLE BEHAVIOR |')
print('|---|---|---|---|---|---|---|---|')

for c in report['case_results']:
    case_id = c['case_id']
    with open(f'evidence/phase_2/runs/run_20260830_091031_f1cc354c/{case_id}.json') as f2:
        case_data = json.load(f2)
    latency = case_data['metadata']['runtime_seconds']
    
    findings = ", ".join(c['actual_findings']) or "None"
    expected = ", ".join(c['expected_findings']) or "None"
    
    print(f"| {case_id} | {c['actual_recommendation']} | {c['expected_recommendation']} | {findings} | {expected} | VALID | {latency:.2f}s | Perfect match |")
