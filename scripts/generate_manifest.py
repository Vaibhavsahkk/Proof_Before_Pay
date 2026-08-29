import hashlib
import glob

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest().upper()

def generate_manifest():
    patterns = [
        'benchmark/schemas/*.json',
        'data/cases/public/*.json',
        'data/cases/ground_truth/*.json',
        'benchmark/RULEBOOK.md'
    ]
    
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
        
    files = [f.replace("\\", "/") for f in files]
    files.sort()
    
    with open("evidence/phase_1/SHA256_MANIFEST.txt", "w", encoding="utf-8") as f:
        f.write("--- PHASE 1 MANIFEST ---\n")
        for file in files:
            h = hash_file(file)
            f.write(f"{h}  {file}\n")
            
    print("Generated evidence/phase_1/SHA256_MANIFEST.txt")

if __name__ == "__main__":
    generate_manifest()
