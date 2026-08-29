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

class ManifestVerifier:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir

    def verify(self):
        manifest_path = os.path.join(self.root_dir, "evidence/phase_1/SHA256_MANIFEST.txt")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
            
        expected_hashes = {}
        with open(manifest_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines or not lines[0].startswith("--- PHASE 1 MANIFEST ---"):
                raise ValueError("Invalid manifest format.")
            for line in lines[1:]:
                line = line.strip()
                if not line: continue
                parts = line.split("  ")
                if len(parts) != 2:
                    raise ValueError(f"Invalid line format: {line}")
                hash_val, path = parts
                if path in expected_hashes:
                    raise ValueError(f"Duplicate entry in manifest: {path}")
                expected_hashes[path] = hash_val
                
        patterns = [
            'benchmark/schemas/*.json',
            'data/cases/public/*.json',
            'data/cases/ground_truth/*.json',
            'benchmark/RULEBOOK.md'
        ]
        
        current_files = []
        for pat in patterns:
            current_files.extend(glob.glob(os.path.join(self.root_dir, pat)))
            
        # Standardize paths to forward slashes for matching, relative to root_dir
        def to_relative(p):
            rel = os.path.relpath(p, self.root_dir)
            return rel.replace("\\", "/")
            
        current_hashes = {to_relative(p): hash_file(p) for p in current_files}
        
        for path, expected_hash in expected_hashes.items():
            if path not in current_hashes:
                raise ValueError(f"Missing file in tree: {path}")
            if current_hashes[path] != expected_hash:
                raise ValueError(f"Hash mismatch for {path}: expected {expected_hash}, got {current_hashes[path]}")
                
        for path in current_hashes:
            if path not in expected_hashes:
                raise ValueError(f"Extra file found in tree not in manifest: {path}")

def verify_manifest():
    try:
        verifier = ManifestVerifier()
        verifier.verify()
        print("Manifest verification passed.")
    except Exception as e:
        print(f"[FAIL] Manifest Verification Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    verify_manifest()
