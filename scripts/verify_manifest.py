import hashlib
import sys
import os
import glob

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().replace("\r\n", "\n")
        sha256.update(content.encode('utf-8'))
    return sha256.hexdigest().upper()

def verify_manifest():
    manifest_path = "evidence/phase_1/SHA256_MANIFEST.txt"
    if not os.path.exists(manifest_path):
        print(f"Manifest not found: {manifest_path}")
        sys.exit(1)
        
    expected_hashes = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines or not lines[0].startswith("--- PHASE 1 MANIFEST ---"):
            print("Invalid manifest format.")
            sys.exit(1)
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            parts = line.split("  ")
            if len(parts) != 2:
                print(f"Invalid line format: {line}")
                sys.exit(1)
            hash_val, path = parts
            expected_hashes[path] = hash_val
            
    # Compute current hashes
    patterns = [
        'benchmark/schemas/*.json',
        'data/cases/public/*.json',
        'data/cases/ground_truth/*.json',
        'benchmark/RULEBOOK.md'
    ]
    
    current_files = []
    for pat in patterns:
        current_files.extend(glob.glob(pat))
        
    # Standardize paths to forward slashes for matching
    current_files = [p.replace("\\", "/") for p in current_files]
    
    current_hashes = {p: hash_file(p) for p in current_files}
    
    # Check for missing or changed
    for path, expected_hash in expected_hashes.items():
        if path not in current_hashes:
            print(f"Missing file in tree: {path}")
            sys.exit(1)
        if current_hashes[path] != expected_hash:
            print(f"Hash mismatch for {path}: expected {expected_hash}, got {current_hashes[path]}")
            sys.exit(1)
            
    # Check for extra files in tree
    for path in current_hashes:
        if path not in expected_hashes:
            print(f"Extra file found in tree not in manifest: {path}")
            sys.exit(1)
            
    print("Manifest verification passed.")

if __name__ == "__main__":
    verify_manifest()
