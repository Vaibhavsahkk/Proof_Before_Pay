import os
import sys
import json
import time
import uuid
import hashlib
import datetime
import importlib.metadata
from pathlib import Path
from jsonschema import validate, ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = BASE_DIR / "data" / "cases" / "public"
RULEBOOK_PATH = BASE_DIR / "benchmark" / "RULEBOOK.md"
SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "output_contract.json"
RUNS_DIR = BASE_DIR / "evidence" / "phase_2" / "runs"
PROMPT_PATH = Path(__file__).resolve().parent / "prompt_v1.txt"

def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest().upper()

def redact_secrets(text: str, api_key: str) -> str:
    if not text:
        return text
    if api_key and api_key in text:
        return text.replace(api_key, "***REDACTED***")
    return text

def write_json_exclusive(path: Path, data: dict):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def run_case(client, model_id, prompt_template, rulebook, schema_obj, case_path, api_key):
    case_id = case_path.stem
    with open(case_path, "r", encoding="utf-8") as f:
        evidence = f.read()
    
    input_hash = compute_sha256(evidence)
    
    prompt = prompt_template.format(
        rulebook=rulebook, 
        evidence=evidence, 
        schema=json.dumps(schema_obj, indent=2)
    )
    prompt_hash = compute_sha256(prompt)
    
    start_time = time.time()
    raw_response = None
    output = None
    status = "SUCCESS"
    error_msg = None
    usage_metadata = None
    returned_model = "UNKNOWN"
    attempt_count = 0
    max_retries = 3

    from google.genai import types
    from google.genai.errors import APIError

    for attempt in range(max_retries):
        attempt_count += 1
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            raw_response = response.text
            returned_model = getattr(response, "model_version", None) or model_id
            usage = getattr(response, "usage_metadata", None)
            if usage:
                usage_metadata = {
                    "prompt_token_count": getattr(usage, "prompt_token_count", None),
                    "candidates_token_count": getattr(usage, "candidates_token_count", None),
                    "total_token_count": getattr(usage, "total_token_count", None)
                }
            break
        except APIError as e:
            # Retry only on transient errors
            is_transient = e.code in [429, 500, 502, 503, 504]
            if not is_transient or attempt == max_retries - 1:
                status = "API_ERROR"
                error_msg = redact_secrets(str(e), api_key)
                raw_response = redact_secrets(str(e), api_key)
                break
            time.sleep(2 ** attempt)
        except Exception as e:
            status = "API_ERROR"
            error_msg = redact_secrets(str(e), api_key)
            raw_response = redact_secrets(str(e), api_key)
            break
            
    latency = time.time() - start_time

    if status == "SUCCESS":
        try:
            output = json.loads(raw_response)
        except Exception as e:
            status = "INVALID_JSON"
            error_msg = redact_secrets(str(e), api_key)
            output = None

    if status == "SUCCESS":
        try:
            validate(instance=output, schema=schema_obj)
        except ValidationError as e:
            status = "SCHEMA_INVALID"
            error_msg = redact_secrets(str(e), api_key)

    if status == "SUCCESS" and output.get("case_id") != case_id:
        status = "CASE_ID_MISMATCH"
        error_msg = f"Expected {case_id}, got {output.get('case_id')}"
        
    try:
        sdk_version = importlib.metadata.version("google-genai")
    except Exception:
        sdk_version = "UNKNOWN"
        
    meta = {
        "provider": "google",
        "requested_model": model_id,
        "returned_model": returned_model,
        "sdk_version": sdk_version,
        "runtime_seconds": latency,
        "prompt_hash": prompt_hash,
        "input_hash": input_hash,
        "usage_metadata": usage_metadata or {
            "prompt_token_count": "UNKNOWN",
            "candidates_token_count": "UNKNOWN",
            "total_token_count": "UNKNOWN"
        },
        "settings": {
            "temperature": 0.0, 
            "response_mime_type": "application/json",
            "max_output_tokens": "UNKNOWN",
            "timeout": "UNKNOWN",
            "safety_settings": "UNKNOWN"
        },
        "retry_policy": "transient_only",
        "attempt_count": attempt_count,
        "cost": "UNKNOWN",
        "status": status,
        "error": error_msg,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "full_request": redact_secrets(prompt, api_key)
    }

    final_output = {
        "case_id": case_id,
        "baseline_output": output,
        "raw_response": raw_response,
        "metadata": meta
    }
    
    return final_output, status

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    from google import genai
    client = genai.Client(api_key=api_key)
    model_id = "gemini-2.5-pro"
    
    if not CASES_DIR.exists():
        print(f"Error: Cases directory {CASES_DIR} not found.", file=sys.stderr)
        sys.exit(1)

    case_files = sorted(CASES_DIR.glob("*.json"))
    expected_cases = {"case_001", "case_002", "case_003", "case_004", "case_005", "case_006"}
    found_cases = {p.stem for p in case_files}
    if found_cases != expected_cases:
        print(f"Error: Cases mismatch. Expected {expected_cases}, found {found_cases}.", file=sys.stderr)
        sys.exit(1)

    with open(RULEBOOK_PATH, "r", encoding="utf-8") as f:
        rulebook = f.read()
    rulebook_hash = compute_sha256(rulebook)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_content = f.read()
        schema_obj = json.loads(schema_content)
    schema_hash = compute_sha256(schema_content)
        
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt_template_hash = compute_sha256(prompt_template)

    run_uuid = str(uuid.uuid4())[:8]
    run_id = "run_" + datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + run_uuid
    run_dir = RUNS_DIR / run_id
    try:
        run_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print(f"Error: Run directory {run_dir} already exists.", file=sys.stderr)
        sys.exit(1)
        
    has_errors = False
    manifest = {
        "run_id": run_id,
        "start_time": datetime.datetime.utcnow().isoformat() + "Z",
        "model": model_id,
        "sdk_version": importlib.metadata.version("google-genai") if importlib.metadata else "UNKNOWN",
        "hashes": {
            "prompt_template_hash": prompt_template_hash,
            "rulebook_hash": rulebook_hash,
            "schema_hash": schema_hash
        },
        "cases": []
    }
    
    for case_file in case_files:
        print(f"Processing {case_file.name}...")
        final_output, status = run_case(client, model_id, prompt_template, rulebook, schema_obj, case_file, api_key)
        
        output_path = run_dir / case_file.name
        write_json_exclusive(output_path, final_output)
        
        manifest["cases"].append({
            "case_id": case_file.stem,
            "input_hash": final_output["metadata"]["input_hash"],
            "status": status
        })
            
        if status != "SUCCESS":
            print(f"Error processing {case_file.name}: {status} - {final_output['metadata'].get('error')}", file=sys.stderr)
            has_errors = True
            
    manifest["end_time"] = datetime.datetime.utcnow().isoformat() + "Z"
    manifest["overall_status"] = "PARTIAL_ERROR" if has_errors else "SUCCESS"
    
    write_json_exclusive(run_dir / "run_manifest.json", manifest)
    print(f"Baseline processing complete. Results saved in {run_dir}")
    if has_errors:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
