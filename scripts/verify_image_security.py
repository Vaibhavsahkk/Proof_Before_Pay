import sys
import subprocess

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.returncode

def main():
    print("Running recursive image security assertion...")
    image_name = "micro1-micro1_app:latest"
    
    cmd = f"docker run --rm {image_name} find /app"
    stdout, rc = run_cmd(cmd)
    
    if rc != 0:
        print(f"Failed to run docker command (exit code {rc}). Ensure image exists and docker is running.")
        sys.exit(1)
        
    files = stdout.split("\n")
    prohibited_patterns = [
        "/.env",
        "/.git",
        "/__pycache__",
        "/.pytest_cache",
        "/traces/raw"
    ]
    
    failed = False
    for f in files:
        # Match exactly against directory components or filename
        for p in prohibited_patterns:
            if f.endswith(p) or p + "/" in f:
                print(f"[FAIL] Found prohibited artifact in image: {f}")
                failed = True
                
    if failed:
        sys.exit(1)
        
    print("[PASS] Image security assertion passed. No prohibited artifacts found.")
    sys.exit(0)

if __name__ == "__main__":
    main()
