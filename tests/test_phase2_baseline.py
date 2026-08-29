import hashlib
import json
import os
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from google.genai.errors import APIError

import baseline.run_baseline as runner
import eval.evaluate_baseline as evaluator
from scripts.verify_manifest import ManifestVerifier


def valid_output(case_id="case_001", recommendation="PAY", findings=None):
    return {
        "case_id": case_id,
        "recommendation": recommendation,
        "findings": findings or [],
        "evidence_references": ["invoice.invoice_id"],
        "deterministic_calculation_references": ["invoice.total"],
        "missing_evidence": [],
        "uncertainty": "No material uncertainty identified.",
        "required_human_next_step": "A human reviewer must make the final decision.",
    }


def actual_schema():
    return json.loads(runner.SCHEMA_PATH.read_text(encoding="utf-8"))


def make_response(payload, model="dummy-model-v1"):
    response = MagicMock()
    response.text = payload if isinstance(payload, str) else json.dumps(payload)
    response.model_version = model
    response.usage_metadata.prompt_token_count = 10
    response.usage_metadata.candidates_token_count = 5
    response.usage_metadata.total_token_count = 15
    return response


def make_client(payload=None, side_effect=None):
    client = MagicMock()
    if side_effect is not None:
        client.models.generate_content.side_effect = side_effect
    else:
        client.models.generate_content.return_value = make_response(
            payload if payload is not None else valid_output()
        )
    return client


class DummyAPIError(APIError):
    def __init__(self, message, code):
        self.message = message
        self.code = code

    def __str__(self):
        return self.message


def run_one(tmp_path, client, api_key="synthetic-secret"):
    case_path = tmp_path / "case_001.json"
    case_path.write_text('{"case_id":"case_001"}', encoding="utf-8")
    return runner.run_case(
        client,
        "test-model",
        "Rule: {rulebook}\nEvidence: {evidence}\nSchema: {schema}",
        "rulebook",
        actual_schema(),
        case_path,
        api_key,
    )


def test_import_without_key_does_not_create_client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = MagicMock()
    monkeypatch.setattr("google.genai.Client", client)
    assert runner.MODEL_ID == "gemini-3.6-flash"
    client.assert_not_called()


def test_missing_key_returns_nonzero_without_creating_evidence(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(runner, "RUNS_DIR", tmp_path / "runs")
    client = MagicMock()
    monkeypatch.setattr("google.genai.Client", client)
    assert runner.main() == 1
    assert not (tmp_path / "runs").exists()
    client.assert_not_called()


def test_prompt_v1_hash_is_literal_and_pinned():
    content = runner.PROMPT_PATH.read_text(encoding="utf-8")
    assert runner.PROMPT_V1_SHA256 == "CA0A31712B6058EE0CFEE0A510740581D6880B0F652F4D9D8AC161FAC8445FD3"
    assert runner.compute_sha256(content) == runner.PROMPT_V1_SHA256


def test_text_file_hash_is_line_ending_independent(tmp_path):
    lf_path = tmp_path / "lf.json"
    crlf_path = tmp_path / "crlf.json"
    lf_path.write_bytes(b'{"case_id":"case_001"}\n')
    crlf_path.write_bytes(b'{"case_id":"case_001"}\r\n')
    assert runner.compute_text_file_sha256(lf_path) == runner.compute_text_file_sha256(
        crlf_path
    )
    assert runner.compute_file_sha256(lf_path) != runner.compute_file_sha256(crlf_path)


def test_prompt_contains_safety_boundaries():
    prompt = runner.PROMPT_PATH.read_text(encoding="utf-8").lower()
    assert "human reviewer" in prompt
    assert "do not execute a payment" in prompt
    assert "declare that any supplier is fraudulent" in prompt


def test_prompt_hash_mismatch_is_rejected(monkeypatch, tmp_path):
    tampered_prompt = tmp_path / "prompt_v1.txt"
    tampered_prompt.write_text(
        runner.PROMPT_PATH.read_text(encoding="utf-8") + "\ntampered",
        encoding="utf-8",
    )
    monkeypatch.setattr(runner, "PROMPT_PATH", tampered_prompt)
    with pytest.raises(ValueError, match="Prompt V1 hash mismatch"):
        runner.load_inputs()


@pytest.mark.parametrize("case_names", [["case_001"], [*(f"case_{i:03d}" for i in range(1, 7)), "case_007"]])
def test_load_inputs_rejects_missing_or_extra_cases(monkeypatch, tmp_path, case_names):
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()
    for case_name in case_names:
        (cases_dir / f"{case_name}.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "CASES_DIR", cases_dir)
    with pytest.raises(ValueError, match="Cases mismatch"):
        runner.load_inputs()


def test_invalid_json_is_preserved_and_fails(tmp_path):
    output, status = run_one(tmp_path, make_client("not json"))
    assert status == "INVALID_JSON"
    assert output["raw_response"] == "not json"
    assert output["baseline_output"] is None


def test_schema_invalid_response_is_preserved_and_fails(tmp_path):
    raw = '{"case_id":"case_001","recommendation":"YES"}'
    output, status = run_one(tmp_path, make_client(raw))
    assert status == "SCHEMA_INVALID"
    assert output["raw_response"] == raw


def test_response_case_id_mismatch_fails(tmp_path):
    output, status = run_one(tmp_path, make_client(valid_output("case_002")))
    assert status == "CASE_ID_MISMATCH"
    assert output["baseline_output"]["case_id"] == "case_002"


def test_api_key_is_redacted_from_every_serialized_field(tmp_path):
    key = "synthetic-secret-key"
    client = make_client(side_effect=Exception(f"provider failed with {key}"))
    output, status = run_one(tmp_path, client, key)
    serialized = json.dumps(output)
    assert status == "API_ERROR"
    assert key not in serialized
    assert "***REDACTED***" in serialized


def test_transient_error_retries_then_succeeds(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.time, "sleep", MagicMock())
    client = make_client(
        side_effect=[
            DummyAPIError("temporary", 429),
            make_response(valid_output()),
        ]
    )
    output, status = run_one(tmp_path, client)
    assert status == "SUCCESS"
    assert output["metadata"]["attempt_count"] == 2
    assert client.models.generate_content.call_count == 2


def test_transient_error_exhaustion_fails_after_three_attempts(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.time, "sleep", MagicMock())
    client = make_client(side_effect=DummyAPIError("temporary", 503))
    output, status = run_one(tmp_path, client)
    assert status == "API_ERROR"
    assert output["metadata"]["attempt_count"] == runner.MAX_ATTEMPTS
    assert client.models.generate_content.call_count == runner.MAX_ATTEMPTS


def test_non_transient_error_is_not_retried(monkeypatch, tmp_path):
    sleep = MagicMock()
    monkeypatch.setattr(runner.time, "sleep", sleep)
    client = make_client(side_effect=DummyAPIError("bad request", 400))
    output, status = run_one(tmp_path, client)
    assert status == "API_ERROR"
    assert output["metadata"]["attempt_count"] == 1
    assert client.models.generate_content.call_count == 1
    sleep.assert_not_called()


def test_success_preserves_raw_response_and_metadata(tmp_path):
    payload = valid_output()
    raw = json.dumps(payload, separators=(",", ":"))
    output, status = run_one(tmp_path, make_client(raw))
    assert status == "SUCCESS"
    assert output["raw_response"] == raw
    assert output["metadata"]["returned_model"] == "dummy-model-v1"
    assert output["metadata"]["usage_metadata"]["total_token_count"] == 15
    assert output["metadata"]["settings"] == runner.GENERATION_SETTINGS
    assert output["metadata"]["runtime_seconds"] >= 0


def test_exclusive_writer_refuses_overwrite(tmp_path):
    path = tmp_path / "result.json"
    first_hash = runner.write_json_exclusive(path, {"value": 1})
    assert first_hash == runner.compute_file_sha256(path)
    with pytest.raises(FileExistsError):
        runner.write_json_exclusive(path, {"value": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"value": 1}


def prepare_runner_files(monkeypatch, tmp_path):
    cases_dir = tmp_path / "public"
    cases_dir.mkdir()
    for case_id in runner.EXPECTED_CASE_IDS:
        (cases_dir / f"{case_id}.json").write_text(
            json.dumps({"case_id": case_id}), encoding="utf-8"
        )
    prompt_path = tmp_path / "prompt_v1.txt"
    prompt_path.write_text(runner.PROMPT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    rulebook_path = tmp_path / "RULEBOOK.md"
    rulebook_path.write_text("Use the supplied evidence.", encoding="utf-8")
    schema_path = tmp_path / "output_contract.json"
    schema_path.write_text(json.dumps(actual_schema()), encoding="utf-8")
    monkeypatch.setattr(runner, "CASES_DIR", cases_dir)
    monkeypatch.setattr(runner, "PROMPT_PATH", prompt_path)
    monkeypatch.setattr(runner, "RULEBOOK_PATH", rulebook_path)
    monkeypatch.setattr(runner, "SCHEMA_PATH", schema_path)
    monkeypatch.setattr(runner, "RUNS_DIR", tmp_path / "runs")


def test_main_generates_complete_six_case_manifest(monkeypatch, tmp_path):
    prepare_runner_files(monkeypatch, tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-key")
    client = make_client()

    def response_for_prompt(**kwargs):
        match = re.search(r'"case_id"\s*:\s*"(case_\d{3})"', kwargs["contents"])
        assert match
        return make_response(valid_output(match.group(1)))

    client.models.generate_content.side_effect = response_for_prompt
    monkeypatch.setattr("google.genai.Client", lambda api_key: client)
    monkeypatch.setattr(
        runner,
        "get_source_state",
        lambda: {"commit_sha": "a" * 40, "working_tree_dirty": False},
    )
    assert runner.main() == 0
    run_dirs = list((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1
    manifest = json.loads((run_dirs[0] / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_schema_version"] == runner.MANIFEST_SCHEMA_VERSION
    assert manifest["input_hash_mode"] == runner.INPUT_HASH_MODE
    assert manifest["expected_case_ids"] == list(runner.EXPECTED_CASE_IDS)
    assert manifest["source"] == {"commit_sha": "a" * 40, "working_tree_dirty": False}
    assert [item["case_id"] for item in manifest["cases"]] == list(runner.EXPECTED_CASE_IDS)
    assert all(item["status"] == "SUCCESS" for item in manifest["cases"])
    for item in manifest["cases"]:
        assert item["output_sha256"] == runner.compute_file_sha256(
            run_dirs[0] / item["output_file"]
        )


def test_main_rejects_dirty_source_before_client_or_evidence(monkeypatch, tmp_path):
    prepare_runner_files(monkeypatch, tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-key")
    monkeypatch.setattr(
        runner,
        "get_source_state",
        lambda: {"commit_sha": "a" * 40, "working_tree_dirty": True},
    )
    client = MagicMock()
    monkeypatch.setattr("google.genai.Client", client)
    assert runner.main() == 1
    assert not (tmp_path / "runs").exists()
    client.assert_not_called()


def prepare_evaluation_run(monkeypatch, tmp_path):
    base_dir = tmp_path / "project"
    run_dir = base_dir / "evidence" / "phase_2" / "runs" / "run_test"
    public_dir = base_dir / "data" / "cases" / "public"
    truth_dir = base_dir / "data" / "cases" / "ground_truth"
    schema_path = base_dir / "benchmark" / "schemas" / "output_contract.json"
    run_dir.mkdir(parents=True)
    public_dir.mkdir(parents=True)
    truth_dir.mkdir(parents=True)
    schema_path.parent.mkdir(parents=True)
    schema_path.write_text(json.dumps(actual_schema()), encoding="utf-8")

    records = []
    for index, case_id in enumerate(runner.EXPECTED_CASE_IDS, start=1):
        public_path = public_dir / f"{case_id}.json"
        public_path.write_text(json.dumps({"case_id": case_id}), encoding="utf-8")
        expected = "HOLD" if index <= 3 else "PAY"
        (truth_dir / f"{case_id}.json").write_text(
            json.dumps(
                {
                    "case_id": case_id,
                    "expected_recommendation": expected,
                    "expected_findings": [],
                }
            ),
            encoding="utf-8",
        )
        baseline_output = valid_output(case_id, "PAY")
        full_request = f"Stable synthetic prompt for {case_id}"
        usage_metadata = {
            "prompt_token_count": 10,
            "candidates_token_count": 5,
            "total_token_count": 15,
        }
        wrapper = {
            "case_id": case_id,
            "baseline_output": baseline_output,
            "raw_response": json.dumps(baseline_output),
            "metadata": {
                "status": "SUCCESS",
                "provider": "google",
                "requested_model": runner.MODEL_ID,
                "returned_model": runner.MODEL_ID,
                "sdk_version": "test-sdk",
                "settings": dict(runner.GENERATION_SETTINGS),
                "input_sha256": runner.compute_text_file_sha256(public_path),
                "input_hash_mode": runner.INPUT_HASH_MODE,
                "runtime_seconds": 1.0,
                "usage_metadata": usage_metadata,
                "retry_policy": "transient_only",
                "attempt_count": 1,
                "full_request": full_request,
                "rendered_prompt_sha256": runner.compute_sha256(full_request),
            },
        }
        output_path = run_dir / f"{case_id}.json"
        output_hash = runner.write_json_exclusive(output_path, wrapper)
        records.append(
            {
                "case_id": case_id,
                "input_sha256": runner.compute_text_file_sha256(public_path),
                "output_file": output_path.name,
                "output_sha256": output_hash,
                "status": "SUCCESS",
                "returned_model": runner.MODEL_ID,
                "usage_metadata": usage_metadata,
            }
        )

    manifest = {
        "manifest_schema_version": runner.MANIFEST_SCHEMA_VERSION,
        "input_hash_mode": runner.INPUT_HASH_MODE,
        "run_id": "run_test",
        "start_time_utc": "2026-08-29T00:00:00Z",
        "end_time_utc": "2026-08-29T00:00:01Z",
        "provider": "google",
        "requested_model": runner.MODEL_ID,
        "sdk_version": "test-sdk",
        "python_version": "3.12",
        "source": {"commit_sha": "a" * 40, "working_tree_dirty": False},
        "command": "python -m baseline.run_baseline",
        "hashes": {
            "prompt_template_sha256": runner.compute_sha256(
                evaluator.PROMPT_PATH.read_text(encoding="utf-8")
            ),
            "rulebook_sha256": runner.compute_sha256(
                evaluator.RULEBOOK_PATH.read_text(encoding="utf-8")
            ),
            "output_schema_sha256": runner.compute_sha256(
                schema_path.read_text(encoding="utf-8")
            ),
            "runner_sha256": runner.compute_file_sha256(evaluator.RUNNER_PATH),
        },
        "settings": dict(runner.GENERATION_SETTINGS),
        "retry_policy": {
            "maximum_attempts": runner.MAX_ATTEMPTS,
            "retryable_http_codes": [429, 500, 502, 503, 504],
            "backoff_seconds": [1, 2],
        },
        "expected_case_ids": list(runner.EXPECTED_CASE_IDS),
        "cases": records,
        "overall_status": "SUCCESS",
    }
    (run_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    monkeypatch.setattr(evaluator, "BASE_DIR", base_dir)
    monkeypatch.setattr(evaluator, "PUBLIC_CASES_DIR", public_dir)
    monkeypatch.setattr(evaluator, "GROUND_TRUTH_DIR", truth_dir)
    monkeypatch.setattr(evaluator, "SCHEMA_PATH", schema_path)
    monkeypatch.setattr(evaluator.ManifestVerifier, "verify", lambda self: None)
    return run_dir


def rewrite_case_and_hash(run_dir, case_id, mutate):
    output_path = run_dir / f"{case_id}.json"
    wrapper = json.loads(output_path.read_text(encoding="utf-8"))
    mutate(wrapper)
    output_path.write_text(
        json.dumps(wrapper, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["cases"]:
        if record["case_id"] == case_id:
            record["output_sha256"] = runner.compute_file_sha256(output_path)
            record["status"] = wrapper["metadata"]["status"]
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


@pytest.mark.parametrize("remove_case,add_extra", [("case_006", False), (None, True)])
def test_evaluator_rejects_missing_or_extra_case(monkeypatch, tmp_path, remove_case, add_extra):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    if remove_case:
        os.remove(run_dir / f"{remove_case}.json")
    if add_extra:
        (run_dir / "case_007.json").write_text("{}", encoding="utf-8")
    with pytest.raises(evaluator.EvaluationError, match="Run files mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_wrapper_case_id_mismatch(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    rewrite_case_and_hash(run_dir, "case_001", lambda value: value.update(case_id="case_002"))
    with pytest.raises(evaluator.EvaluationError, match="Wrapper case_id mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_output_case_id_mismatch(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)

    def mutate(value):
        value["baseline_output"]["case_id"] = "case_002"

    rewrite_case_and_hash(run_dir, "case_001", mutate)
    with pytest.raises(evaluator.EvaluationError, match="Baseline output case_id mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_raw_response_mismatch(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    rewrite_case_and_hash(
        run_dir,
        "case_001",
        lambda value: value.update(raw_response=json.dumps(valid_output("case_001", "HOLD"))),
    )
    with pytest.raises(evaluator.EvaluationError, match="Raw response mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_rendered_prompt_hash_mismatch(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)

    def mutate(value):
        value["metadata"]["rendered_prompt_sha256"] = "0" * 64

    rewrite_case_and_hash(run_dir, "case_001", mutate)
    with pytest.raises(evaluator.EvaluationError, match="Rendered prompt hash mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_returned_model_mismatch(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)

    def mutate(value):
        value["metadata"]["returned_model"] = "different-model"

    rewrite_case_and_hash(run_dir, "case_001", mutate)
    with pytest.raises(evaluator.EvaluationError, match="Wrapper returned model mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_usage_metadata_mismatch(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)

    def mutate(value):
        value["metadata"]["usage_metadata"]["prompt_token_count"] += 1

    rewrite_case_and_hash(run_dir, "case_001", mutate)
    with pytest.raises(evaluator.EvaluationError, match="Wrapper usage metadata mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_output_hash_tampering(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    with (run_dir / "case_001.json").open("a", encoding="utf-8") as handle:
        handle.write(" ")
    with pytest.raises(evaluator.EvaluationError, match="Output hash mismatch"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_rejects_dirty_or_mismatched_source_manifest(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source"]["working_tree_dirty"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(evaluator.EvaluationError, match="clean source tree"):
        evaluator.evaluate_baseline(str(run_dir))

    manifest["source"]["working_tree_dirty"] = False
    manifest["hashes"]["prompt_template_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(evaluator.EvaluationError, match="source-artifact hashes"):
        evaluator.evaluate_baseline(str(run_dir))


def test_evaluator_schema_invalid_is_reported_and_fails(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)

    def mutate(value):
        value["baseline_output"] = {"case_id": "case_001", "recommendation": "PAY"}
        value["metadata"]["status"] = "SCHEMA_INVALID"

    rewrite_case_and_hash(run_dir, "case_001", mutate)
    with pytest.raises(evaluator.EvaluationError, match="Run is invalid"):
        evaluator.evaluate_baseline(str(run_dir))
    report = json.loads((run_dir / "evaluation_report.json").read_text(encoding="utf-8"))
    assert report["evaluation_status"] == "INVALID"
    assert report["metrics"]["schema_valid_rate_percent"] < 100


def test_evaluator_metrics_are_exact_and_ordered(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    report = evaluator.evaluate_baseline(str(run_dir))
    metrics = report["metrics"]
    assert metrics["exact_case_level_recommendation_accuracy_percent"] == 50.0
    assert metrics["unsafe_pay_count"] == 3
    assert metrics["unsafe_pay_rate_percent"] == 100.0
    assert metrics["schema_valid_rate_percent"] == 100.0
    assert metrics["latency"] == {"total_seconds": 6.0, "mean_seconds": 1.0}
    assert metrics["tokens"] == {
        "total_prompt_tokens": 60,
        "total_candidates_tokens": 30,
    }
    assert [item["case_id"] for item in report["case_results"]] == list(
        runner.EXPECTED_CASE_IDS
    )


def test_evaluator_refuses_to_overwrite_report(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    evaluator.evaluate_baseline(str(run_dir))
    with pytest.raises(evaluator.EvaluationError, match="already exists"):
        evaluator.evaluate_baseline(str(run_dir))


def test_existing_report_verification_is_deterministic(monkeypatch, tmp_path):
    run_dir = prepare_evaluation_run(monkeypatch, tmp_path)
    expected_report = evaluator.evaluate_baseline(str(run_dir))
    source_files = {
        "baseline/prompt_v1.txt": evaluator.PROMPT_PATH,
        "benchmark/RULEBOOK.md": evaluator.RULEBOOK_PATH,
        "benchmark/schemas/output_contract.json": evaluator.SCHEMA_PATH,
        "baseline/run_baseline.py": evaluator.RUNNER_PATH,
    }

    def fake_git_show(command, **_kwargs):
        repository_path = command[-1].split(":", maxsplit=1)[1]
        return MagicMock(stdout=source_files[repository_path].read_bytes())

    monkeypatch.setattr(evaluator.subprocess, "run", fake_git_show)
    assert evaluator.verify_existing_report(str(run_dir)) == expected_report

    report_path = run_dir / "evaluation_report.json"
    tampered_report = json.loads(report_path.read_text(encoding="utf-8"))
    tampered_report["metrics"]["unsafe_pay_count"] = 0
    report_path.write_text(json.dumps(tampered_report), encoding="utf-8")
    with pytest.raises(evaluator.EvaluationError, match="deterministic re-evaluation"):
        evaluator.verify_existing_report(str(run_dir))


def test_phase_1_manifest_canonical_hash_is_exact_and_verifies():
    manifest_path = runner.BASE_DIR / "evidence" / "phase_1" / "SHA256_MANIFEST.txt"
    canonical_bytes = manifest_path.read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(canonical_bytes).hexdigest().upper() == (
        "EEF0BDF46D385F9BC47E14AF4E188DACE2B2E03B9510793E62D04706E03DAABE"
    )
    ManifestVerifier(str(runner.BASE_DIR)).verify()


def test_runtime_dockerfile_uses_allowlist_and_compose_has_no_credentials():
    dockerfile = (runner.BASE_DIR / "Dockerfile").read_text(encoding="utf-8")
    runtime = dockerfile.split("FROM base AS runtime", maxsplit=1)[1]
    assert "data/cases/public/" in runtime
    assert "baseline/" in runtime
    for prohibited in ("ground_truth", "eval/", "tests/", "evidence/"):
        assert prohibited not in runtime
    compose = (runner.BASE_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    for credential in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        assert credential not in compose
