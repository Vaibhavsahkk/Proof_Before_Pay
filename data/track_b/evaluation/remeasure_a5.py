"""Run a fresh Track B baseline/agent comparison and score it offline.

This runner creates new immutable run directories through ``run_track_b.py``
and then invokes ``evaluate_track_b.py``. It never edits the frozen dataset or
historical run artifacts.

Two hard requirements it enforces before spending any quota:

1. QUOTA PRE-CHECK — a single 1-token probe against the agent's extraction
   model. If the free-tier daily quota (or any 429/RESOURCE_EXHAUSTED) is
   hit, the runner prints the provider's reset/quota message and exits 3
   ("run after quota reset") instead of burning a partial 12-case run.
2. TRACK B CACHE CLEARING — the agent's extraction/explanation caches for
   the 12 Track B cases are removed so every case measures the FIXED
   extractor live, never a stale (possibly pre-fix) cache entry.

Usage:
    python data/track_b/evaluation/remeasure_a5.py [--prompt-version v2]
        [--out reports/track_b_remeasured_results.json] [--keep-cache]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parents[2]
RUN_PATTERN = re.compile(r"Run complete:\s+.*[\\/](?:baseline|agent)_runs[\\/](run_[^\s]+)")

# The 12 frozen Track B cases (case_101..case_112).
TRACK_B_CASES = [f"case_{n}" for n in range(101, 113)]

# Extraction model recorded by the A4 agent-version freeze. The probe uses
# the same model bucket whose quota the full run will consume.
A4_FREEZE = REPO_ROOT / "evidence" / "phase_track_b" / "A4_agent_version_freeze.json"


def probe_quota():
    """One minimal live call against the extraction model.

    Returns (ok, message). ok=False means the provider is refusing requests
    (429/quota exhausted); the message is the provider's own error text so
    the operator sees the exact reset/quota guidance."""
    sys.path.insert(0, str(REPO_ROOT))
    # Load .env the same way the agent does (never print key values).
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
    except ImportError:
        pass
    from google import genai
    from src.agent.credentials import CredentialManager

    model_id = "gemini-3.6-flash"
    try:
        freeze = json.loads(A4_FREEZE.read_text(encoding="utf-8"))
        recorded = (freeze.get("models") or {}).get("extraction")
        if isinstance(recorded, str) and recorded:
            model_id = recorded
    except Exception:
        pass

    cred = CredentialManager()
    key = cred.get_current_key()
    client = genai.Client(api_key=key)
    try:
        response = client.models.generate_content(
            model=model_id,
            contents="Reply with exactly: OK",
        )
        text = (response.text or "").strip()
        return True, f"probe OK (model={model_id}, reply={text[:20]!r})"
    except Exception as exc:
        return False, f"probe FAILED (model={model_id}): {str(exc)[:400]}"


def clear_track_b_caches():
    """Remove agent extraction/explanation caches for the 12 Track B cases
    so the re-measurement exercises the fixed extractor live. Returns the
    list of removed paths (for the log)."""
    removed = []
    for case in TRACK_B_CASES:
        for sub in ("extractions", "explanations"):
            path = REPO_ROOT / "data" / "cache" / sub / f"{case}.json"
            if path.is_file():
                path.unlink()
                removed.append(str(path.relative_to(REPO_ROOT)).replace("\\", "/"))
    return removed


def run_mode(mode, prompt_version):
    command = [sys.executable, str(EVAL_DIR / "run_track_b.py"), "--mode", mode]
    if mode == "baseline":
        command.extend(["--prompt-version", prompt_version])
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True,
                               capture_output=True)
    output = completed.stdout + completed.stderr
    print(output, end="")
    if completed.returncode:
        raise SystemExit(f"{mode} run failed with exit {completed.returncode}")
    match = RUN_PATTERN.search(completed.stdout)
    if not match:
        raise SystemExit(f"Could not identify {mode} run directory from runner output")
    return match.group(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt-version", choices=["v1", "v2"], default="v2")
    parser.add_argument("--out", default="reports/track_b_remeasured_results.json")
    parser.add_argument("--keep-cache", action="store_true",
                        help="skip Track B cache clearing (uses existing caches)")
    args = parser.parse_args()

    # --- 1. Quota pre-check -------------------------------------------
    print("[remeasure] step 1/4: quota pre-check on the extraction model")
    ok, message = probe_quota()
    print(f"[remeasure] {message}")
    if not ok:
        print("[remeasure] ABORTED: provider quota/rate limit reached. "
              "Run again after the quota reset (typically daily for the "
              "free tier). No partial run was started, no quota spent "
              "beyond the probe.")
        return 3

    # --- 2. Cache clearing --------------------------------------------
    if args.keep_cache:
        print("[remeasure] step 2/4: cache clearing SKIPPED (--keep-cache)")
    else:
        removed = clear_track_b_caches()
        print(f"[remeasure] step 2/4: cleared {len(removed)} Track B cache "
              f"entries ({', '.join(removed[:4])}{'...' if len(removed) > 4 else ''})")

    # --- 3. Fresh runs -------------------------------------------------
    print("[remeasure] step 3/4: fresh baseline + agent runs")
    baseline_run = run_mode("baseline", args.prompt_version)
    agent_run = run_mode("agent", args.prompt_version)

    # --- 4. Offline scoring --------------------------------------------
    print("[remeasure] step 4/4: offline scoring")
    command = [
        sys.executable,
        str(EVAL_DIR / "evaluate_track_b.py"),
        "--baseline-run", baseline_run,
        "--agent-run", agent_run,
        "--out", args.out,
    ]
    completed = subprocess.run(command, cwd=REPO_ROOT, text=True)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
