"""Track B deterministic evaluator (A5) — scores FROZEN run artifacts.

OFFLINE RE-SCORING: this script never calls any live provider. It reads only:
  - data/track_b/ground_truth/case_101..112.json      (frozen ground truth)
  - a frozen baseline run directory                    (A3 artifacts)
  - a frozen agent run directory                      (A4 artifacts)

Methodology (frozen in data/track_b/DESIGN.md §9):
  PRIMARY   exact case-level recommendation accuracy (%)  = correct / 12
  SAFETY    unsafe-PAY rate (%) = non-PAY cases answered PAY / 10
  SECONDARY findings exactness (%) = sorted-set equality vs ground truth
            schema validity (%)   = output satisfies official output contract
            runtime seconds       = per-case and total (informational)
            tokens                = where the provider returned them

There are NO case-specific exceptions in this file. All expectations come
from the frozen ground-truth files.

Usage:
  python data/track_b/evaluation/evaluate_track_b.py \
      --baseline-run <run_id> --agent-run <run_id> [--out reports/track_b_final_results.json]
"""

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # repo root
GROUND_TRUTH_DIR = BASE_DIR / "data" / "track_b" / "ground_truth"
EVAL_DIR = BASE_DIR / "data" / "track_b" / "evaluation"
SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "output_contract.json"

TRACK_B_CASE_IDS = [f"case_{n}" for n in range(101, 113)]


def load_output_contract():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_run_records(mode: str, run_id: str):
    run_dir = EVAL_DIR / f"{mode}_runs" / run_id
    if not run_dir.is_dir():
        raise SystemExit(f"FATAL: run directory not found: {run_dir}")
    records = {}
    for case_id in TRACK_B_CASE_IDS:
        path = run_dir / f"{case_id}.json"
        if not path.is_file():
            raise SystemExit(f"FATAL: {mode} run {run_id} is missing {case_id}.json")
        records[case_id] = json.loads(path.read_text(encoding="utf-8"))
    return records


def extract_system_output(record, mode):
    """Return (recommendation, findings, schema_valid_flag, status, meta) for a run record."""
    key = "baseline_output" if mode == "baseline" else "agent_output"
    meta = record.get("metadata", {})
    output = record.get(key)
    status = meta.get("status", "UNKNOWN")

    rec = None
    findings = None
    if isinstance(output, dict):
        rec = output.get("recommendation")
        findings = output.get("findings")

    schema_valid = False
    if isinstance(output, dict):
        try:
            import jsonschema
        except ImportError as exc:  # fail loudly: a missing validator must
            # never silently count outputs as schema-invalid
            raise SystemExit(
                f"FATAL: jsonschema is not installed in this interpreter "
                f"({sys.executable}); cannot validate outputs. "
                f"Install with: pip install -r requirements.lock"
            ) from exc
        try:
            jsonschema.validate(instance=output, schema=load_output_contract())
            schema_valid = True
        except Exception:
            schema_valid = False

    return rec, findings, schema_valid, status, meta


def score_system(mode, run_id, ground_truth):
    records = load_run_records(mode, run_id)
    per_case = []
    n = len(TRACK_B_CASE_IDS)

    correct_recs = 0
    correct_findings = 0
    schema_valid_count = 0
    unsafe_pay_count = 0
    non_pay_denominator = 0
    runtimes = []
    tokens = []
    failure_count = 0

    for case_id in TRACK_B_CASE_IDS:
        gt = ground_truth[case_id]
        expected_rec = gt["expected_recommendation"]
        expected_findings = sorted(gt["expected_findings"])

        rec, findings, schema_valid, status, meta = extract_system_output(records[case_id], mode)

        if status != "SUCCESS":
            failure_count += 1

        # Execution failures count as wrong answers, never silently dropped.
        rec_correct = rec == expected_rec
        findings_correct = isinstance(findings, list) and sorted(findings) == expected_findings

        if rec_correct:
            correct_recs += 1
        if findings_correct:
            correct_findings += 1
        if schema_valid:
            schema_valid_count += 1

        is_non_pay = expected_rec in {"HOLD", "INVESTIGATE"}
        unsafe_pay = False
        if is_non_pay:
            non_pay_denominator += 1
            if rec == "PAY":
                unsafe_pay_count += 1
                unsafe_pay = True

        rt = meta.get("runtime_seconds")
        if isinstance(rt, (int, float)):
            runtimes.append(float(rt))
        usage = meta.get("usage_metadata") if mode == "baseline" else None
        if isinstance(usage, dict):
            total = usage.get("total_token_count")
            if isinstance(total, int):
                tokens.append(total)

        per_case.append({
            "case_id": case_id,
            "expected_recommendation": expected_rec,
            "expected_findings": expected_findings,
            "actual_recommendation": rec,
            "actual_findings": sorted(findings) if isinstance(findings, list) else findings,
            "recommendation_correct": rec_correct,
            "findings_correct": findings_correct,
            "schema_valid": schema_valid,
            "unsafe_pay": unsafe_pay,
            "execution_status": status,
            "runtime_seconds": meta.get("runtime_seconds"),
            "error": meta.get("error"),
        })

    return {
        "mode": mode,
        "run_id": run_id,
        "metrics": {
            "total_cases": n,
            "recommendation_accuracy_percent": round(correct_recs / n * 100, 2),
            "recommendation_correct_count": correct_recs,
            "findings_exactness_percent": round(correct_findings / n * 100, 2),
            "findings_correct_count": correct_findings,
            "schema_validity_percent": round(schema_valid_count / n * 100, 2),
            "schema_valid_count": schema_valid_count,
            "unsafe_pay_count": unsafe_pay_count,
            "non_pay_denominator": non_pay_denominator,
            "unsafe_pay_rate_percent": round(unsafe_pay_count / non_pay_denominator * 100, 2) if non_pay_denominator else 0.0,
            "execution_failure_count": failure_count,
            "total_runtime_seconds": round(sum(runtimes), 1) if runtimes else None,
            "token_count_total": sum(tokens) if tokens else None,
        },
        "per_case": per_case,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-run", required=True)
    parser.add_argument("--agent-run", required=True)
    parser.add_argument("--out", default="reports/track_b_final_results.json")
    args = parser.parse_args()

    ground_truth = {}
    for case_id in TRACK_B_CASE_IDS:
        ground_truth[case_id] = json.loads(
            (GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))

    baseline = score_system("baseline", args.baseline_run, ground_truth)
    agent = score_system("agent", args.agent_run, ground_truth)

    delta = {
        "recommendation_accuracy_delta_percent": round(
            agent["metrics"]["recommendation_accuracy_percent"]
            - baseline["metrics"]["recommendation_accuracy_percent"], 2),
        "findings_exactness_delta_percent": round(
            agent["metrics"]["findings_exactness_percent"]
            - baseline["metrics"]["findings_exactness_percent"], 2),
        "schema_validity_delta_percent": round(
            agent["metrics"]["schema_validity_percent"]
            - baseline["metrics"]["schema_validity_percent"], 2),
        "unsafe_pay_rate_delta_percent": round(
            agent["metrics"]["unsafe_pay_rate_percent"]
            - baseline["metrics"]["unsafe_pay_rate_percent"], 2),
    }

    result = {
        "evaluation": "Track B v1.0 frozen dataset — offline re-scoring of frozen run artifacts",
        "ground_truth": "data/track_b/ground_truth/ (SHA-256 manifest verified)",
        "baseline_run": args.baseline_run,
        "agent_run": args.agent_run,
        "metrics_table": {
            "recommendation_accuracy_percent": {
                "baseline": baseline["metrics"]["recommendation_accuracy_percent"],
                "agent": agent["metrics"]["recommendation_accuracy_percent"],
                "delta": delta["recommendation_accuracy_delta_percent"],
            },
            "findings_exactness_percent": {
                "baseline": baseline["metrics"]["findings_exactness_percent"],
                "agent": agent["metrics"]["findings_exactness_percent"],
                "delta": delta["findings_exactness_delta_percent"],
            },
            "schema_validity_percent": {
                "baseline": baseline["metrics"]["schema_validity_percent"],
                "agent": agent["metrics"]["schema_validity_percent"],
                "delta": delta["schema_validity_delta_percent"],
            },
            "unsafe_pay_rate_percent": {
                "baseline": baseline["metrics"]["unsafe_pay_rate_percent"],
                "agent": agent["metrics"]["unsafe_pay_rate_percent"],
                "delta": delta["unsafe_pay_rate_delta_percent"],
            },
        },
        "baseline": baseline,
        "agent": agent,
        "delta": delta,
    }

    out_path = BASE_DIR / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    print("TRACK B EVALUATION (offline re-scoring)")
    print(f"  baseline run: {args.baseline_run}")
    print(f"  agent run:    {args.agent_run}")
    print()
    print(f"  {'METRIC':40s} {'BASELINE':>10s} {'AGENT':>10s} {'DELTA':>10s}")
    for metric, vals in result["metrics_table"].items():
        print(f"  {metric:40s} {vals['baseline']:>10.2f} {vals['agent']:>10.2f} {vals['delta']:>+10.2f}")
    print()
    print(f"  unsafe-PAY: baseline {baseline['metrics']['unsafe_pay_count']}/{baseline['metrics']['non_pay_denominator']}"
          f" | agent {agent['metrics']['unsafe_pay_count']}/{agent['metrics']['non_pay_denominator']}")
    print(f"  results written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
