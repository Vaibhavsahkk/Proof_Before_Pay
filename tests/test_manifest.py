import pytest
import os
import json
import hashlib
from scripts.verify_manifest import ManifestVerifier

def create_fake_manifest_env(tmp_path):
    # Create the required tree
    (tmp_path / "evidence/phase_1").mkdir(parents=True, exist_ok=True)
    (tmp_path / "benchmark/schemas").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/cases/public").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/cases/ground_truth").mkdir(parents=True, exist_ok=True)
    (tmp_path / "benchmark").mkdir(parents=True, exist_ok=True)
    
    # Create dummy files
    rulebook = tmp_path / "benchmark/RULEBOOK.md"
    rulebook.write_text("rulebook")
    
    schema = tmp_path / "benchmark/schemas/public_evidence_bundle.json"
    schema.write_text("{}")
    
    # Hash function matching verifier
    def get_hash(p):
        sha256 = hashlib.sha256()
        with open(p, "r", encoding="utf-8") as f:
            content = f.read().replace("\r\n", "\n")
            sha256.update(content.encode('utf-8'))
        return sha256.hexdigest().upper()
        
    manifest_lines = [
        "--- PHASE 1 MANIFEST ---",
        f"{get_hash(rulebook)}  benchmark/RULEBOOK.md",
        f"{get_hash(schema)}  benchmark/schemas/public_evidence_bundle.json"
    ]
    
    manifest_path = tmp_path / "evidence/phase_1/SHA256_MANIFEST.txt"
    manifest_path.write_text("\n".join(manifest_lines) + "\n")
    return tmp_path

def test_manifest_success(tmp_path):
    env = create_fake_manifest_env(tmp_path)
    verifier = ManifestVerifier(root_dir=str(env))
    verifier.verify() # Should not raise

def test_manifest_missing_file(tmp_path):
    env = create_fake_manifest_env(tmp_path)
    # Delete the rulebook
    (env / "benchmark/RULEBOOK.md").unlink()
    verifier = ManifestVerifier(root_dir=str(env))
    with pytest.raises(ValueError, match="Missing file in tree"):
        verifier.verify()

def test_manifest_hash_mismatch(tmp_path):
    env = create_fake_manifest_env(tmp_path)
    # Mutate the rulebook
    (env / "benchmark/RULEBOOK.md").write_text("mutated")
    verifier = ManifestVerifier(root_dir=str(env))
    with pytest.raises(ValueError, match="Hash mismatch"):
        verifier.verify()

def test_manifest_extra_file(tmp_path):
    env = create_fake_manifest_env(tmp_path)
    # Add an extra file matching the pattern
    (env / "benchmark/schemas/extra.json").write_text("{}")
    verifier = ManifestVerifier(root_dir=str(env))
    with pytest.raises(ValueError, match="Extra file found"):
        verifier.verify()

def test_manifest_duplicate_entry(tmp_path):
    env = create_fake_manifest_env(tmp_path)
    # Duplicate a line in the manifest
    manifest_path = env / "evidence/phase_1/SHA256_MANIFEST.txt"
    content = manifest_path.read_text()
    manifest_path.write_text(content + content.splitlines()[1] + "\n")
    verifier = ManifestVerifier(root_dir=str(env))
    with pytest.raises(ValueError, match="Duplicate entry in manifest"):
        verifier.verify()

def test_manifest_malformed_row(tmp_path):
    env = create_fake_manifest_env(tmp_path)
    # Add a malformed row
    manifest_path = env / "evidence/phase_1/SHA256_MANIFEST.txt"
    manifest_path.write_text(manifest_path.read_text() + "MALFORMED_ROW_NO_SPACES\n")
    verifier = ManifestVerifier(root_dir=str(env))
    with pytest.raises(ValueError, match="Invalid line format"):
        verifier.verify()
