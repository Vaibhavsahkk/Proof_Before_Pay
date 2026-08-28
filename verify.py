import sys
import subprocess
import os

def run_step(step_name, cmd, cwd=None):
    print(f"\n{'='*60}")
    print(f"STEP: {step_name}")
    print(f"COMMAND: {cmd}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    
    if result.returncode != 0:
        print(f"\n[FAIL] Step '{step_name}' failed with exit code {result.returncode}.")
        sys.exit(1)
    
    print(f"\n[PASS] Step '{step_name}' completed successfully.")

def main():
    print("Starting Micro1 Challenge Verification Pipeline...")
    
    # 1. Clean Dependency Verification
    # (Assuming virtual env setup or pip install -r requirements-dev.txt happened prior,
    # but we can verify pytest is available)
    run_step("Dependency & Env Check", "python -m pytest --version")
    
    # 2. Local Container Tests (Adversarial telemetry tests)
    run_step("Automated Test Suite Execution", "python -m pytest -q")
    
    # 3. Docker Build
    run_step("Docker Build", "docker compose build --no-cache")
    
    # 4. Smoke Execution (via docker compose)
    run_step("Smoke Execution", "docker compose run micro1_app")
    
    # 5. Recursive Image-Security Checks
    run_step("Image Security Assertion", "python scripts/verify_image_security.py")
    
    # 6. Repository Checks
    print("\n" + "="*60)
    print("STEP: Git Tracked Traces Check")
    print("="*60)
    git_result = subprocess.run("git ls-files traces/raw", shell=True, capture_output=True, text=True)
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
