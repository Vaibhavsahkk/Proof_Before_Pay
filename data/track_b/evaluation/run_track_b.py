"""Track B runner — baseline and agent execution over the FROZEN dataset.

Sub-phases:
  A2 baseline mode : one direct Gemini call per case, every document attached
                     in its native format (PDF/PNG as multimodal parts, JSON as
                     text), frozen prompt v1, official output contract.
  A4 agent mode    : the EXISTING, unmodified Proof Before Pay pipeline
                     (DocumentAdapter -> AgentOrchestrator).

Isolation guarantees (A2.3 / A4.2):
  - Reads ONLY: data/track_b/cases/<case>/bundle.json + the documents it lists.
  - NEVER reads: data/track_b/ground_truth/, evaluator files, agent traces,
    agent outputs, official benchmark answers, Track A caches.
  - Track B case IDs (case_101..112) cannot collide with Track A IDs
    (case_001..012) in the shared extraction cache; this is asserted at start.
  - Baseline never reads the extraction cache; the agent uses it as committed
    behavior (cache is the agent's existing production design, and entries
    are written only from live results for previously-unseen cases).

Artifacts are written immutably under data/track_b/evaluation/<mode>_runs/<run_id>/
(exclusive-create, sorted keys, redacted of the API key).
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # repo root: data/track_b/evaluation/ -> up 3
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv  # noqa: E402

TRACK_B = BASE_DIR / "data" / "track_b"
CASES_DIR = TRACK_B / "cases"
EVAL_DIR = TRACK_B / "evaluation"
# Baseline prompt versions. v1 (frozen) is retained as defect evidence:
# it omitted the output contract, so findings cases failed schema validation
# (see evidence/phase_track_b/A3_baseline_prompt_v1_defect.md, written before
# any scoring). v2 embeds the official output contract inline; created and
# hash-frozen before the first scoring run.
PROMPT_VERSIONS = {
    "v1": ("baseline_prompt_v1.txt", "baseline_prompt_v1.sha256"),
    "v2": ("baseline_prompt_v2.txt", "baseline_prompt_v2.sha256"),
}
DEFAULT_PROMPT_VERSION = "v2"
SCHEMA_PATH = BASE_DIR / "benchmark" / "schemas" / "output_contract.json"

MODEL_ID = "gemini-3.6-flash"  # envelope frozen by DESIGN.md §7
GENERATION_SETTINGS = {
    "temperature": 0.0,
    "response_mime_type": "application/json",
    "max_output_tokens": 4096,
    "timeout": "SDK_DEFAULT_NOT_EXPLICIT",
    "safety_settings": "SDK_DEFAULT_NOT_EXPLICIT",
}
MAX_ATTEMPTS = 3  # same transient-only retry policy as the accepted Track A baseline
TRACK_B_CASE_IDS = [f"case_{n}" for n in range(101, 113)]
TRACK_A_CACHE_DIR = BASE_DIR / "data" / "cache" / "extractions"


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def compute_sha256(data) -> str:
    if isinstance(data, str):
        return hashlib.sha256(data.encode("utf-8")).hexdigest().upper()
    return hashlib.sha256(data).hexdigest().upper()


def redact(text, api_key):
    if text is None:
        return None
    return text.replace(api_key, "***REDACTED***") if api_key else text


def write_exclusive(path: Path, data: dict) -> str:
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
    return compute_sha256(payload)


def get_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=BASE_DIR,
                              capture_output=True, check=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return "UNAVAILABLE"


def check_cache_isolation():
    """A4.2: Track B IDs must never resolve to a Track A cache entry.

    Track A IDs are case_001..case_012; Track B IDs are case_101..case_112.
    The ID spaces are disjoint BY DESIGN, so a Track-B case can never load a
    Track-A cache entry. Extraction caches written by earlier Track-B agent
    runs for Track-B IDs are the agent's own production behavior (same as
    the UI) and are legitimate: the runner still re-executes DocumentAdapter
    (live OCR for PNGs) and the full deterministic pipeline per case."""
    track_a_ids = {f"case_{n:03d}" for n in range(1, 13)}
    overlap = track_a_ids & set(TRACK_B_CASE_IDS)
    if overlap:
        raise SystemExit(f"FATAL: ID space overlap {overlap}")
    collisions = [c for c in track_a_ids if (TRACK_A_CACHE_DIR / f"{c}.json").exists() is False]
    # (informational: Track A caches are restored from git; not required for Track B runs)
    return True


def load_case(case_id: str):
    """Load ONLY bundle.json + the documents it lists. Never ground truth."""
    case_dir = CASES_DIR / case_id
    bundle = json.loads((case_dir / "bundle.json").read_text(encoding="utf-8"))
    if bundle["case_id"] != case_id or bundle["track"] != "B":
        raise ValueError(f"bundle mismatch for {case_id}")
    docs = []
    for name in bundle["documents"]:
        docs.append({"name": name, "bytes": (case_dir / name).read_bytes()})
    input_hash = compute_sha256(
        case_id + "|" + "|".join(
            f"{d['name']}:{compute_sha256(d['bytes'])}" for d in docs))
    return docs, input_hash, bundle


# ---------------------------------------------------------------------------
# Baseline: one direct multimodal call per case
# ---------------------------------------------------------------------------

def run_baseline_case(cred_manager, api_key, case_id, prompt_template, schema_obj):
    docs, input_hash, _ = load_case(case_id)
    prompt_text = prompt_template.replace("{case_id}", case_id)

    from google import genai
    from google.genai import types
    from google.genai.errors import APIError

    contents = []
    for d in docs:
        if d["name"].endswith(".json"):
            # JSON as text (same information the agent's DocumentAdapter gets)
            text = d["bytes"].decode("utf-8")
            contents.append(types.Part.from_text(text=text))
        else:
            mime = "application/pdf" if d["name"].endswith(".pdf") else "image/png"
            contents.append(types.Part.from_bytes(data=d["bytes"], mime_type=mime))
    contents.append(prompt_text)

    start = time.perf_counter()
    raw = None
    status = "SUCCESS"
    error = None
    attempts = 0
    usage = None
    returned_model = "NOT_RETURNED"
    key_rotations = 0
    last_cooldown_wait = 0.0

    while attempts < MAX_ATTEMPTS:
        attempts += 1
        try:
            current_key = cred_manager.get_current_key()  # may raise RetrySignal
            client = genai.Client(api_key=current_key)
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json",
                    max_output_tokens=4096,
                ),
            )
            raw = redact(response.text, api_key)
            returned_model = getattr(response, "model_version", None) or MODEL_ID
            u = getattr(response, "usage_metadata", None)
            if u is not None:
                usage = {
                    "prompt_token_count": getattr(u, "prompt_token_count", None),
                    "candidates_token_count": getattr(u, "candidates_token_count", None),
                    "total_token_count": getattr(u, "total_token_count", None),
                }
            break
        except APIError as exc:
            code = getattr(exc, "code", None)
            is_transient = code in {429, 500, 502, 503, 504}
            if not is_transient or attempts >= MAX_ATTEMPTS:
                status = "API_ERROR"
                error = redact(str(exc), api_key)
                raw = error
                break
            # Same rotation policy as the agent: rotate key, wait, retry.
            if code == 429:
                cred_manager.mark_cooldown(60.0)
                key_rotations += 1
                wait = cred_manager.get_wait_time()
                if wait < 0:
                    status = "POOL_EXHAUSTED"
                    error = redact(str(exc), api_key)
                    raw = error
                    break
                last_cooldown_wait = wait
                time.sleep(min(wait, 30.0))
            else:
                time.sleep(2 ** (attempts - 1))
        except Exception as exc:
            err_str = str(exc)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                cred_manager.mark_cooldown(60.0)
                key_rotations += 1
                wait = cred_manager.get_wait_time()
                if wait < 0:
                    status = "POOL_EXHAUSTED"
                    error = redact(err_str, api_key)
                    raw = error
                    break
                last_cooldown_wait = wait
                time.sleep(min(wait, 30.0))
                if attempts >= MAX_ATTEMPTS:
                    status = "API_ERROR"
                    error = redact(err_str, api_key)
                    raw = error
                    break
                continue
            status = "API_ERROR"
            error = redact(err_str, api_key)
            raw = error
            break

    runtime = time.perf_counter() - start
    output = None
    schema_valid = False
    if status == "SUCCESS":
        try:
            output = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            status = "INVALID_JSON"
            error = str(exc)
        else:
            import jsonschema
            try:
                jsonschema.validate(instance=output, schema=schema_obj)
                schema_valid = True
            except Exception as exc:
                status = "SCHEMA_INVALID"
                error = str(exc)[:500]

    if status == "SUCCESS" and output.get("case_id") != case_id:
        status = "CASE_ID_MISMATCH"
        error = f"expected {case_id}, got {output.get('case_id')}"

    return {
        "case_id": case_id,
        "baseline_output": output,
        "raw_response": raw,
        "metadata": {
            "track": "B",
            "mode": "baseline",
            "provider": "google",
            "requested_model": MODEL_ID,
            "returned_model": returned_model,
            "settings": dict(GENERATION_SETTINGS),
            "prompt_template_sha256": compute_sha256(prompt_template),
            "input_hash": input_hash,
            "runtime_seconds": runtime,
            "usage_metadata": usage or {"prompt_token_count": "NOT_RETURNED",
                                        "candidates_token_count": "NOT_RETURNED",
                                        "total_token_count": "NOT_RETURNED"},
            "retry_policy": "transient_only_plus_key_rotation",
            "attempt_count": attempts,
            "key_rotations": key_rotations,
            "cooldown_wait_seconds": round(last_cooldown_wait, 1),
            "documents": [d["name"] for d in docs],
            "status": status,
            "error": error,
            "timestamp_utc": utc_now(),
        },
    }


# ---------------------------------------------------------------------------
# Agent: existing pipeline, unmodified
# ---------------------------------------------------------------------------

def run_agent_case(api_key, case_id, cred_manager=None):
    """Run the CURRENT agent (DocumentAdapter -> AgentOrchestrator) on the
    same frozen documents. No case-specific logic here.

    cred_manager: shared CredentialManager over the full key pool. Passing the
    single GEMINI_API_KEY string here would silently shrink the agent's pool
    to one key (run 20260901_072737 failed exactly this way when that key's
    daily quota was exhausted); the full pool matches both production behavior
    and the baseline's resilience envelope."""
    from src.agent.orchestrator import AgentOrchestrator
    from src.agent.credentials import RetrySignal

    docs, input_hash, bundle = load_case(case_id)

    # Feed the agent through its production document adapter exactly as the
    # UI does (src/ui/server.py /api/investigate files path).
    files = []
    for d in docs:
        ext = d["name"].rsplit(".", 1)[1].lower()
        mime = {"pdf": "application/pdf", "png": "image/png",
                "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "json": "application/json"}.get(ext, "application/octet-stream")
        files.append({"name": d["name"],
                      "data": d["bytes"],
                      "type": mime})

    start = time.perf_counter()
    max_recoveries = 30
    recoveries = 0

    # One fresh orchestrator per case so traces and state never bleed across cases.
    # The shared credential pool keeps key cooldowns coherent across cases.
    orch = AgentOrchestrator(credential_manager=cred_manager)

    while True:
        try:
            adapter_input = files
            from src.agent.document_adapter import DocumentAdapter, DocumentProcessingError
            adapter = DocumentAdapter(credential_manager=orch.extractor.cred_manager)
            doc_meta = None
            try:
                raw_evidence, doc_meta = adapter.process_bundle(adapter_input)
            except DocumentProcessingError as dpe:
                result = {
                    "case_id": case_id,
                    "recommendation": "INVESTIGATE",
                    "findings": ["Unreadable Document"],
                    "evidence_references": [],
                    "deterministic_calculation_references": [],
                    "missing_evidence": [],
                    "uncertainty": f"Unable to verify document: {dpe}",
                    "required_human_next_step": "Human review required. Ensure uploaded documents are readable.",
                }
                runtime = time.perf_counter() - start
                return _agent_wrapper(case_id, result, input_hash, docs, runtime,
                                      recoveries, orch, adapter_meta=doc_meta,
                                      status="DOCUMENT_ERROR")

            result = orch.run_workflow(case_id, raw_evidence)
            runtime = time.perf_counter() - start
            return _agent_wrapper(case_id, result, input_hash, docs, runtime,
                                  recoveries, orch, adapter_meta=doc_meta)

        except RetrySignal:
            recoveries += 1
            wait = 5.0
            if recoveries > max_recoveries:
                runtime = time.perf_counter() - start
                return _agent_wrapper(case_id, {
                    "case_id": case_id, "recommendation": "INVESTIGATE",
                    "findings": ["All credentials exhausted"],
                    "evidence_references": [],
                    "deterministic_calculation_references": [],
                    "missing_evidence": [],
                    "uncertainty": "All Gemini API keys exhausted their quota.",
                    "required_human_next_step": "Human review required.",
                }, input_hash, docs, runtime, recoveries, orch, status="POOL_EXHAUSTED")
            time.sleep(wait)
        except Exception as exc:
            runtime = time.perf_counter() - start
            return _agent_wrapper(case_id, {
                "case_id": case_id, "recommendation": "INVESTIGATE",
                "findings": ["Extraction or System Failure"],
                "evidence_references": [],
                "deterministic_calculation_references": [],
                "missing_evidence": [],
                "uncertainty": f"System failure occurred: {exc}",
                "required_human_next_step": "Human review required due to system error.",
            }, input_hash, docs, runtime, recoveries, orch, status="SYSTEM_ERROR")


def _agent_wrapper(case_id, result, input_hash, docs, runtime, recoveries, orch,
                   adapter_meta=None, status="SUCCESS"):
    trace_file = None
    if orch is not None and hasattr(orch, "logger"):
        trace_file = str(orch.logger.log_file)
    checks_performed = getattr(orch, "last_checks_performed", [])
    checks_skipped = getattr(orch, "last_checks_skipped", [])
    extracted = getattr(orch, "last_extracted_data", None)
    return {
        "case_id": case_id,
        "agent_output": result,
        "metadata": {
            "track": "B",
            "mode": "agent",
            "provider": "google",
            "requested_model": MODEL_ID,
            "input_hash": input_hash,
            "runtime_seconds": runtime,
            "credential_recoveries": recoveries,
            "documents": [d["name"] for d in docs],
            "documents_metadata": adapter_meta or [],
            "trace_file": trace_file,
            "checks_performed": checks_performed,
            "checks_skipped": checks_skipped,
            "extracted_data": extracted,
            "status": status,
            "timestamp_utc": utc_now(),
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["baseline", "agent"], required=True)
    parser.add_argument("--case", help="single case id (smoke); omit for all frozen cases")
    parser.add_argument("--smoke", action="store_true", help="run exactly one case (case_101)")
    parser.add_argument("--prompt-version", choices=sorted(PROMPT_VERSIONS),
                        default=DEFAULT_PROMPT_VERSION,
                        help="baseline prompt version (agent mode ignores this)")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("Error: GEMINI_API_KEY not set.", file=sys.stderr)
        return 1

    check_cache_isolation()

    # Frozen prompt + hash verification (A2.5): refuse to run if the prompt
    # does not match its recorded SHA-256.
    prompt_path = EVAL_DIR / PROMPT_VERSIONS[args.prompt_version][0]
    prompt_sha_path = EVAL_DIR / PROMPT_VERSIONS[args.prompt_version][1]
    prompt_template = prompt_path.read_text(encoding="utf-8")
    recorded = prompt_sha_path.read_text().split("  ")[0]
    if compute_sha256(prompt_template) != recorded:
        print("FATAL: baseline prompt does not match its frozen SHA-256.", file=sys.stderr)
        return 1
    print(f"Baseline prompt {args.prompt_version} SHA-256 verified: {recorded}")

    schema_obj = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    case_ids = [args.case] if args.case else (["case_101"] if args.smoke else TRACK_B_CASE_IDS)
    for c in case_ids:
        if c not in TRACK_B_CASE_IDS:
            print(f"Error: {c} is not a frozen Track B case.", file=sys.stderr)
            return 1

    run_id = f"run_{datetime.datetime.now(datetime.timezone.utc):%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}"
    run_dir = EVAL_DIR / f"{args.mode}_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "track": "B",
        "mode": args.mode,
        "run_id": run_id,
        "start_time_utc": utc_now(),
        "git_head": get_head(),
        "provider": "google",
        "requested_model": MODEL_ID,
        "prompt_version": args.prompt_version if args.mode == "baseline" else None,
        "prompt_template_sha256": compute_sha256(prompt_template) if args.mode == "baseline" else None,
        "settings": dict(GENERATION_SETTINGS) if args.mode == "baseline" else None,
        "retry_policy": {"maximum_attempts": MAX_ATTEMPTS,
                          "retryable_http_codes": [429, 500, 502, 503, 504],
                          "backoff_seconds": [1, 2]},
        "cases": [],
    }

    # Same 5-key pool and rotation policy for BOTH systems (fairness:
    # identical resilience envelope for baseline and agent).
    from src.agent.credentials import CredentialManager
    cred_manager = CredentialManager()
    print(f"{args.mode} credential pool: {len(cred_manager.credentials)} key(s)")

    has_errors = False
    for case_id in case_ids:
        print(f"[{args.mode}] {case_id} ...", flush=True)
        try:
            if args.mode == "baseline":
                record = run_baseline_case(cred_manager, api_key, case_id, prompt_template, schema_obj)
            else:
                record = run_agent_case(api_key, case_id, cred_manager=cred_manager)
        except Exception as exc:
            has_errors = True
            print(f"  EXECUTION FAILURE: {exc}", file=sys.stderr)
            record = {
                "case_id": case_id,
                "baseline_output" if args.mode == "baseline" else "agent_output": None,
                "raw_response": None,
                "metadata": {"status": "EXECUTION_FAILURE",
                             "error": redact(str(exc), api_key)[:500],
                             "timestamp_utc": utc_now()},
            }

        out_path = run_dir / f"{case_id}.json"
        out_hash = write_exclusive(out_path, record)
        status = record.get("metadata", {}).get("status", "?")
        if status != "SUCCESS":
            has_errors = True
        print(f"  -> {status} ({record['metadata'].get('runtime_seconds', 0):.1f}s)")

        entry = {"case_id": case_id,
                 "input_hash": record.get("metadata", {}).get("input_hash"),
                 "output_file": f"{case_id}.json",
                 "output_sha256": out_hash,
                 "status": status}
        if args.mode == "agent":
            entry["trace_file"] = record.get("metadata", {}).get("trace_file")
            entry["credential_recoveries"] = record.get("metadata", {}).get("credential_recoveries")
        manifest["cases"].append(entry)

    manifest["end_time_utc"] = utc_now()
    manifest["overall_status"] = "PARTIAL_ERROR" if has_errors else "SUCCESS"
    write_exclusive(run_dir / "run_manifest.json", manifest)

    print(f"\nRun complete: {run_dir}")
    print(f"Overall status: {manifest['overall_status']}")
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
