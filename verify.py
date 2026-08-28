import sys
import subprocess
import os

def run_step(step_name, cmd_list, cwd=None, timeout=300):
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"COMMAND: {' '.join(cmd_list)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd_list, cwd=cwd, timeout=timeout, capture_output=True, text=True, encoding='utf-8')
    except subprocess.TimeoutExpired:
        print(f"\n[FAIL] Step '{step_name}' timed out after {timeout} seconds.")
        sys.exit(1)
        
    if result.returncode != 0:
        print(f"\n[FAIL] Step '{step_name}' failed with exit code {result.returncode}.")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        sys.exit(1)
    
    print(f"\n[PASS] Step '{step_name}' completed successfully.")
    print(f"STDOUT:\n{result.stdout.encode('ascii', 'replace').decode('ascii').strip()}")
    if result.stderr.strip():
        print(f"STDERR:\n{result.stderr.encode('ascii', 'replace').decode('ascii').strip()}")
    return result.stdout

def main():
    print("Starting Micro1 Challenge Verification Pipeline...")
    
    # 1. Docker Build (Explicitly using ONLY docker-compose.yml)
    run_step("Docker Build", ["docker", "compose", "-f", "docker-compose.yml", "build", "--no-cache"])
    
    # 2. Local Container Tests (Adversarial telemetry tests inside Docker)
    run_step("Automated Test Suite Execution (Docker-driven)", ["docker", "compose", "-f", "docker-compose.yml", "run", "--rm", "micro1_app", "sh", "-c", "pip install --user -r requirements-dev.txt && python -m pytest -q"])
    
    # 4. Verify Compose Configuration Isolation (Ensure no host mounts)
    config_out = run_step("Compose Config Isolation Check", ["docker", "compose", "-f", "docker-compose.yml", "config"])
    if "/app/src" in config_out or "type: bind" in config_out:
        print("[FAIL] Found unexpected bind mounts in docker-compose.yml.")
        sys.exit(1)
    
    # 5. Smoke Execution (via docker compose run --rm)
    run_step("Smoke Execution", ["docker", "compose", "-f", "docker-compose.yml", "run", "--rm", "micro1_app"])
    
    # 6. Recursive Image-Security Checks
    run_step("Image Security Assertion", [sys.executable, "scripts/verify_image_security.py"])
    
    # 7. Repository Checks
    print("\n" + "="*60)
    print("STEP: Git Tracked Traces Check")
    print("="*60)
    git_result = subprocess.run(["git", "ls-files", "traces/raw"], capture_output=True, text=True, encoding='utf-8')
    if git_result.stdout.strip():
        print(f"[FAIL] Found tracked raw traces:\n{git_result.stdout}")
        sys.exit(1)
    else:
        print("[PASS] Step 'Git Tracked Traces Check' completed successfully.")
    
    print("\n" + "*"*60)
    print("ALL VERIFICATION STEPS PASSED")
    print("*"*60)
    sys.exit(0)

if __name__ == "__main__":
    main()
