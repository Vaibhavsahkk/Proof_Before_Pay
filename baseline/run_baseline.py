import datetime
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from pathlib import Path

from jsonschema import ValidationError, validate


BASE_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = BASE_DIR / "data" / "cases" / "public"
RULEBOOK_PATH = BASE_DIR / "benchmark" / "RULEBOOK.md"
SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "output_contract.json"
RUNS_DIR = BASE_DIR / "evidence" / "phase_2" / "runs"
PROMPT_PATH = Path(__file__).resolve().parent / "prompt_v1.txt"

EXPECTED_CASE_IDS = tuple(f"case_{number:03d}" for number in range(1, 7))
PROMPT_V1_SHA256 = "CA0A31712B6058EE0CFEE0A510740581D6880B0F652F4D9D8AC161FAC8445FD3"
MODEL_ID = "gemini-3.1-pro-preview"
MAX_ATTEMPTS = 3
GENERATION_SETTINGS = {
    "temperature": 0.0,
    "response_mime_type": "application/json",
    "max_output_tokens": 4096,
    "timeout": "SDK_DEFAULT_NOT_EXPLICIT",
    "safety_settings": "SDK_DEFAULT_NOT_EXPLICIT",
}


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest().upper()


def compute_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def redact_secrets(text: str | None, api_key: str) -> str | None:
    if text is None or not api_key:
        return text
    return text.replace(api_key, "***REDACTED***")


def write_json_exclusive(path: Path, data: dict) -> str:
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    return compute_sha256(payload)


def get_sdk_version() -> str:
    try:
        return importlib.metadata.version("google-genai")
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def get_source_state() -> dict:
    result = {"commit_sha": "UNAVAILABLE", "working_tree_dirty": "UNKNOWN"}
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=BASE_DIR,
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=BASE_DIR,
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        result["commit_sha"] = commit.stdout.strip()
        result["working_tree_dirty"] = bool(status.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return result


def run_case(client, model_id, prompt_template, rulebook, schema_obj, case_path, api_key):
    case_id = case_path.stem
    evidence = case_path.read_text(encoding="utf-8")
    input_hash = compute_file_sha256(case_path)
    prompt = prompt_template.format(
        rulebook=rulebook,
        evidence=evidence,
        schema=json.dumps(schema_obj, indent=2, sort_keys=True),
    )
    prompt_hash = compute_sha256(prompt)

    start_time = time.perf_counter()
    raw_response = None
    output = None
    status = "SUCCESS"
    error_msg = None
    usage_metadata = None
    returned_model = "NOT_RETURNED"
    attempt_count = 0

    from google.genai import types
    from google.genai.errors import APIError

    for attempt in range(MAX_ATTEMPTS):
        attempt_count += 1
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type=GENERATION_SETTINGS["response_mime_type"],
                    temperature=GENERATION_SETTINGS["temperature"],
                    max_output_tokens=GENERATION_SETTINGS["max_output_tokens"],
                ),
            )
            raw_response = redact_secrets(response.text, api_key)
            returned_model = getattr(response, "model_version", None) or model_id
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                usage_metadata = {
                    "prompt_token_count": getattr(usage, "prompt_token_count", None),
                    "candidates_token_count": getattr(usage, "candidates_token_count", None),
                    "total_token_count": getattr(usage, "total_token_count", None),
                }
            break
        except APIError as exc:
            code = getattr(exc, "code", None)
            is_transient = code in {429, 500, 502, 503, 504}
            if not is_transient or attempt == MAX_ATTEMPTS - 1:
                status = "API_ERROR"
                error_msg = redact_secrets(str(exc), api_key)
                raw_response = error_msg
                break
            time.sleep(2**attempt)
        except Exception as exc:
            status = "API_ERROR"
            error_msg = redact_secrets(str(exc), api_key)
            raw_response = error_msg
            break

    latency = time.perf_counter() - start_time

    if status == "SUCCESS":
        try:
            output = json.loads(raw_response)
        except (TypeError, json.JSONDecodeError) as exc:
            status = "INVALID_JSON"
            error_msg = redact_secrets(str(exc), api_key)

    if status == "SUCCESS":
        try:
            validate(instance=output, schema=schema_obj)
        except ValidationError as exc:
            status = "SCHEMA_INVALID"
            error_msg = redact_secrets(exc.message, api_key)

    if status == "SUCCESS" and output["case_id"] != case_id:
        status = "CASE_ID_MISMATCH"
        error_msg = f"Expected {case_id}, got {output['case_id']}"

    metadata = {
        "provider": "google",
        "requested_model": model_id,
        "returned_model": returned_model,
        "sdk_version": get_sdk_version(),
        "runtime_seconds": latency,
        "rendered_prompt_sha256": prompt_hash,
        "input_sha256": input_hash,
        "usage_metadata": usage_metadata
        or {
            "prompt_token_count": "NOT_RETURNED",
            "candidates_token_count": "NOT_RETURNED",
            "total_token_count": "NOT_RETURNED",
        },
        "settings": dict(GENERATION_SETTINGS),
        "retry_policy": "transient_only",
        "attempt_count": attempt_count,
        "cost": "UNKNOWN",
        "status": status,
        "error": error_msg,
        "timestamp_utc": utc_now(),
        "full_request": redact_secrets(prompt, api_key),
    }
    final_output = {
        "case_id": case_id,
        "baseline_output": output,
        "raw_response": raw_response,
        "metadata": metadata,
    }
    return final_output, status


def load_inputs():
    if not CASES_DIR.is_dir():
        raise ValueError(f"Cases directory not found: {CASES_DIR}")
    case_files = sorted(CASES_DIR.glob("*.json"))
    found_cases = tuple(path.stem for path in case_files)
    if found_cases != EXPECTED_CASE_IDS:
        raise ValueError(
            f"Cases mismatch. Expected {list(EXPECTED_CASE_IDS)}, found {list(found_cases)}"
        )

    rulebook = RULEBOOK_PATH.read_text(encoding="utf-8")
    schema_content = SCHEMA_PATH.read_text(encoding="utf-8")
    schema_obj = json.loads(schema_content)
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt_hash = compute_sha256(prompt_template)
    if prompt_hash != PROMPT_V1_SHA256:
        raise ValueError(
            f"Prompt V1 hash mismatch. Expected {PROMPT_V1_SHA256}, got {prompt_hash}"
        )
    return case_files, rulebook, schema_content, schema_obj, prompt_template


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        return 1

    try:
        case_files, rulebook, schema_content, schema_obj, prompt_template = load_inputs()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    source_state = get_source_state()
    if (
        not isinstance(source_state.get("commit_sha"), str)
        or len(source_state["commit_sha"]) != 40
        or source_state.get("working_tree_dirty") is not False
    ):
        print("Error: The baseline must run from a clean committed Git source state.", file=sys.stderr)
        return 1

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
    except Exception as exc:
        print(f"Error creating Gemini client: {redact_secrets(str(exc), api_key)}", file=sys.stderr)
        return 1

    run_id = f"run_{datetime.datetime.now(datetime.timezone.utc):%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    run_dir = RUNS_DIR / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except (FileExistsError, OSError) as exc:
        print(f"Error creating run directory: {exc}", file=sys.stderr)
        return 1

    manifest = {
        "manifest_schema_version": "phase2-baseline-run-v1",
        "run_id": run_id,
        "start_time_utc": utc_now(),
        "provider": "google",
        "requested_model": MODEL_ID,
        "sdk_version": get_sdk_version(),
        "python_version": platform.python_version(),
        "source": source_state,
        "command": "python -m baseline.run_baseline",
        "hashes": {
            "prompt_template_sha256": compute_sha256(prompt_template),
            "rulebook_sha256": compute_sha256(rulebook),
            "output_schema_sha256": compute_sha256(schema_content),
            "runner_sha256": compute_file_sha256(Path(__file__)),
        },
        "settings": dict(GENERATION_SETTINGS),
        "retry_policy": {
            "maximum_attempts": MAX_ATTEMPTS,
            "retryable_http_codes": [429, 500, 502, 503, 504],
            "backoff_seconds": [1, 2],
        },
        "expected_case_ids": list(EXPECTED_CASE_IDS),
        "cases": [],
    }

    has_errors = False
    for case_file in case_files:
        print(f"Processing {case_file.name}...")
        final_output, status = run_case(
            client,
            MODEL_ID,
            prompt_template,
            rulebook,
            schema_obj,
            case_file,
            api_key,
        )
        output_path = run_dir / case_file.name
        output_hash = write_json_exclusive(output_path, final_output)
        manifest["cases"].append(
            {
                "case_id": case_file.stem,
                "input_sha256": final_output["metadata"]["input_sha256"],
                "output_file": case_file.name,
                "output_sha256": output_hash,
                "status": status,
                "returned_model": final_output["metadata"]["returned_model"],
                "usage_metadata": final_output["metadata"]["usage_metadata"],
            }
        )
        if status != "SUCCESS":
            print(
                f"Error processing {case_file.name}: {status} - "
                f"{final_output['metadata']['error']}",
                file=sys.stderr,
            )
            has_errors = True

    manifest["end_time_utc"] = utc_now()
    manifest["overall_status"] = "PARTIAL_ERROR" if has_errors else "SUCCESS"
    write_json_exclusive(run_dir / "run_manifest.json", manifest)
    print(f"Baseline processing complete. Results saved in {run_dir}")
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
