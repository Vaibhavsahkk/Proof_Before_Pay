import argparse
import json
import sys
from pathlib import Path

from jsonschema import ValidationError, validate

from baseline.run_baseline import (
    EXPECTED_CASE_IDS,
    GENERATION_SETTINGS,
    MODEL_ID,
    PROMPT_PATH,
    RULEBOOK_PATH,
    compute_file_sha256,
    compute_sha256,
    write_json_exclusive,
)
from scripts.verify_manifest import ManifestVerifier


BASE_DIR = Path(__file__).resolve().parent.parent
GROUND_TRUTH_DIR = BASE_DIR / "data" / "cases" / "ground_truth"
PUBLIC_CASES_DIR = BASE_DIR / "data" / "cases" / "public"
SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "output_contract.json"
RUNNER_PATH = BASE_DIR / "baseline" / "run_baseline.py"


class EvaluationError(ValueError):
    pass


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"Expected a JSON object in {path}")
    return value


def validate_manifest(manifest: dict, run_path: Path) -> dict:
    required = {
        "manifest_schema_version",
        "run_id",
        "start_time_utc",
        "end_time_utc",
        "provider",
        "requested_model",
        "sdk_version",
        "python_version",
        "source",
        "command",
        "hashes",
        "settings",
        "retry_policy",
        "expected_case_ids",
        "cases",
        "overall_status",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise EvaluationError(f"Manifest missing required fields: {missing}")
    if manifest["manifest_schema_version"] != "phase2-baseline-run-v1":
        raise EvaluationError("Unsupported Phase 2 manifest schema version")
    if manifest["provider"] != "google" or manifest["requested_model"] != MODEL_ID:
        raise EvaluationError("Manifest provider or requested model does not match the baseline")
    if manifest["settings"] != GENERATION_SETTINGS:
        raise EvaluationError("Manifest generation settings do not match the baseline")
    source = manifest["source"]
    if not isinstance(source, dict):
        raise EvaluationError("Manifest source must be an object")
    if not isinstance(source.get("commit_sha"), str) or len(source["commit_sha"]) != 40:
        raise EvaluationError("Manifest source commit SHA is invalid")
    if source.get("working_tree_dirty") is not False:
        raise EvaluationError("Baseline must be run from a clean source tree")

    hashes = manifest["hashes"]
    if not isinstance(hashes, dict):
        raise EvaluationError("Manifest hashes must be an object")
    expected_hashes = {
        "prompt_template_sha256": compute_sha256(PROMPT_PATH.read_text(encoding="utf-8")),
        "rulebook_sha256": compute_sha256(RULEBOOK_PATH.read_text(encoding="utf-8")),
        "output_schema_sha256": compute_sha256(SCHEMA_PATH.read_text(encoding="utf-8")),
        "runner_sha256": compute_file_sha256(RUNNER_PATH),
    }
    if hashes != expected_hashes:
        raise EvaluationError("Manifest source-artifact hashes do not match current files")
    if manifest["expected_case_ids"] != list(EXPECTED_CASE_IDS):
        raise EvaluationError("Manifest expected_case_ids is not the frozen six-case sequence")
    if not isinstance(manifest["cases"], list):
        raise EvaluationError("Manifest cases must be a list")

    records = {}
    for record in manifest["cases"]:
        if not isinstance(record, dict):
            raise EvaluationError("Every manifest case record must be an object")
        case_id = record.get("case_id")
        if case_id in records:
            raise EvaluationError(f"Duplicate manifest case: {case_id}")
        if case_id not in EXPECTED_CASE_IDS:
            raise EvaluationError(f"Unexpected manifest case: {case_id}")
        expected_file = f"{case_id}.json"
        if record.get("output_file") != expected_file:
            raise EvaluationError(f"Manifest output filename mismatch for {case_id}")
        for field in ("input_sha256", "output_sha256", "status"):
            if not isinstance(record.get(field), str) or not record[field]:
                raise EvaluationError(f"Manifest {case_id} missing {field}")
        records[case_id] = record

    if tuple(sorted(records)) != EXPECTED_CASE_IDS:
        raise EvaluationError("Manifest does not contain exactly the six frozen cases")

    files = sorted(path.name for path in run_path.glob("case_*.json"))
    expected_files = [f"{case_id}.json" for case_id in EXPECTED_CASE_IDS]
    if files != expected_files:
        raise EvaluationError(f"Run files mismatch. Expected {expected_files}, found {files}")
    return records


def evaluate_baseline(run_dir: str) -> dict:
    run_path = Path(run_dir)
    if not run_path.is_dir():
        raise EvaluationError(f"Run directory not found: {run_path}")
    report_path = run_path / "evaluation_report.json"
    if report_path.exists():
        raise EvaluationError(f"Evaluation report already exists: {report_path}")

    try:
        ManifestVerifier(str(BASE_DIR)).verify()
    except Exception as exc:
        raise EvaluationError(f"Frozen Phase 1 manifest verification failed: {exc}") from exc

    manifest_path = run_path / "run_manifest.json"
    if not manifest_path.is_file():
        raise EvaluationError(f"run_manifest.json not found in {run_path}")
    manifest = read_json(manifest_path)
    manifest_records = validate_manifest(manifest, run_path)
    schema_obj = read_json(SCHEMA_PATH)

    case_results = []
    invalid_reasons = []
    correct_recommendations = 0
    unsafe_pay_count = 0
    total_non_pay_cases = 0
    correct_findings_count = 0
    total_latency = 0.0
    total_prompt_tokens = 0
    total_candidates_tokens = 0
    schema_valid_count = 0

    for case_id in EXPECTED_CASE_IDS:
        output_path = run_path / f"{case_id}.json"
        ground_truth_path = GROUND_TRUTH_DIR / f"{case_id}.json"
        public_case_path = PUBLIC_CASES_DIR / f"{case_id}.json"
        if not ground_truth_path.is_file():
            raise EvaluationError(f"Missing ground truth for {case_id}")
        if not public_case_path.is_file():
            raise EvaluationError(f"Missing public input for {case_id}")

        record = manifest_records[case_id]
        actual_output_hash = compute_file_sha256(output_path)
        if record["output_sha256"] != actual_output_hash:
            raise EvaluationError(f"Output hash mismatch for {case_id}")
        actual_input_hash = compute_file_sha256(public_case_path)
        if record["input_sha256"] != actual_input_hash:
            raise EvaluationError(f"Input hash mismatch for {case_id}")

        out_data = read_json(output_path)
        ground_truth = read_json(ground_truth_path)
        if out_data.get("case_id") != case_id:
            raise EvaluationError(f"Wrapper case_id mismatch for {case_id}")
        if ground_truth.get("case_id") != case_id:
            raise EvaluationError(f"Ground-truth case_id mismatch for {case_id}")

        metadata = out_data.get("metadata")
        if not isinstance(metadata, dict):
            raise EvaluationError(f"Missing metadata object for {case_id}")
        status = metadata.get("status")
        if status != record["status"]:
            raise EvaluationError(f"Manifest status mismatch for {case_id}")
        if metadata.get("input_sha256") != record["input_sha256"]:
            raise EvaluationError(f"Wrapper input hash mismatch for {case_id}")
        if metadata.get("provider") != manifest["provider"]:
            raise EvaluationError(f"Wrapper provider mismatch for {case_id}")
        if metadata.get("requested_model") != manifest["requested_model"]:
            raise EvaluationError(f"Wrapper requested model mismatch for {case_id}")
        if metadata.get("settings") != manifest["settings"]:
            raise EvaluationError(f"Wrapper settings mismatch for {case_id}")

        baseline_output = out_data.get("baseline_output")
        schema_valid = False
        if isinstance(baseline_output, dict):
            output_case_id = baseline_output.get("case_id")
            if output_case_id != case_id:
                raise EvaluationError(f"Baseline output case_id mismatch for {case_id}")
            try:
                validate(instance=baseline_output, schema=schema_obj)
                schema_valid = True
                schema_valid_count += 1
            except ValidationError as exc:
                invalid_reasons.append(f"{case_id}:SCHEMA_INVALID:{exc.message}")
        else:
            invalid_reasons.append(f"{case_id}:NO_VALID_OUTPUT_OBJECT")

        if status != "SUCCESS":
            invalid_reasons.append(f"{case_id}:STATUS_{status}")
        if status == "SUCCESS" and not schema_valid:
            invalid_reasons.append(f"{case_id}:SUCCESS_WITH_INVALID_SCHEMA")

        expected_recommendation = ground_truth["expected_recommendation"]
        expected_findings = sorted(ground_truth.get("expected_findings", []))
        actual_recommendation = (
            baseline_output.get("recommendation") if isinstance(baseline_output, dict) else None
        )
        actual_findings = sorted(
            baseline_output.get("findings", []) if isinstance(baseline_output, dict) else []
        )

        recommendation_correct = (
            status == "SUCCESS"
            and schema_valid
            and actual_recommendation == expected_recommendation
        )
        findings_correct = (
            status == "SUCCESS" and schema_valid and actual_findings == expected_findings
        )
        if recommendation_correct:
            correct_recommendations += 1
        if findings_correct:
            correct_findings_count += 1

        is_non_pay = expected_recommendation in {"HOLD", "INVESTIGATE"}
        is_unsafe_pay = is_non_pay and actual_recommendation == "PAY"
        if is_non_pay:
            total_non_pay_cases += 1
        if is_unsafe_pay:
            unsafe_pay_count += 1

        runtime_seconds = metadata.get("runtime_seconds", 0.0)
        if isinstance(runtime_seconds, (int, float)) and not isinstance(runtime_seconds, bool):
            total_latency += float(runtime_seconds)
        usage = metadata.get("usage_metadata", {})
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_token_count")
            candidate_tokens = usage.get("candidates_token_count")
            if isinstance(prompt_tokens, int) and not isinstance(prompt_tokens, bool):
                total_prompt_tokens += prompt_tokens
            if isinstance(candidate_tokens, int) and not isinstance(candidate_tokens, bool):
                total_candidates_tokens += candidate_tokens

        case_results.append(
            {
                "case_id": case_id,
                "expected_recommendation": expected_recommendation,
                "actual_recommendation": actual_recommendation,
                "status": status,
                "schema_valid": schema_valid,
                "recommendation_correct": recommendation_correct,
                "expected_findings": expected_findings,
                "actual_findings": actual_findings,
                "findings_correct": findings_correct,
                "is_unsafe_pay": is_unsafe_pay,
            }
        )

    if manifest.get("overall_status") != "SUCCESS":
        invalid_reasons.append(f"MANIFEST_STATUS_{manifest.get('overall_status')}")

    total_cases = len(EXPECTED_CASE_IDS)
    report = {
        "report_schema_version": "phase2-baseline-evaluation-v1",
        "run_id": manifest["run_id"],
        "evaluation_status": "INVALID" if invalid_reasons else "VALID",
        "invalid_reasons": sorted(set(invalid_reasons)),
        "metrics": {
            "total_cases": total_cases,
            "exact_case_level_recommendation_accuracy_percent": (
                correct_recommendations / total_cases * 100
            ),
            "unsafe_pay_rate_percent": (
                unsafe_pay_count / total_non_pay_cases * 100
                if total_non_pay_cases
                else 0.0
            ),
            "findings_correctness_percent": correct_findings_count / total_cases * 100,
            "schema_valid_rate_percent": schema_valid_count / total_cases * 100,
            "unsafe_pay_count": unsafe_pay_count,
            "total_non_pay_cases": total_non_pay_cases,
            "latency": {
                "total_seconds": total_latency,
                "mean_seconds": total_latency / total_cases,
            },
            "tokens": {
                "total_prompt_tokens": total_prompt_tokens,
                "total_candidates_tokens": total_candidates_tokens,
            },
            "cost": "UNKNOWN",
        },
        "case_results": case_results,
    }
    write_json_exclusive(report_path, report)
    if invalid_reasons:
        raise EvaluationError(
            f"Run is invalid; report written to {report_path}: {sorted(set(invalid_reasons))}"
        )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "run_dir",
        help="Run directory containing baseline outputs and run_manifest.json",
    )
    args = parser.parse_args(argv)
    try:
        report = evaluate_baseline(args.run_dir)
    except EvaluationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    metrics = report["metrics"]
    print("=== Phase 2 Baseline Evaluation ===")
    print(f"Run ID: {report['run_id']}")
    print(f"Total Cases: {metrics['total_cases']}")
    print(
        "Exact Case-Level Recommendation Accuracy: "
        f"{metrics['exact_case_level_recommendation_accuracy_percent']:.2f}%"
    )
    print(
        f"Unsafe-PAY Rate: {metrics['unsafe_pay_rate_percent']:.2f}% "
        f"({metrics['unsafe_pay_count']}/{metrics['total_non_pay_cases']})"
    )
    print(f"Schema Valid Rate: {metrics['schema_valid_rate_percent']:.2f}%")
    print(f"Findings Correctness: {metrics['findings_correctness_percent']:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
