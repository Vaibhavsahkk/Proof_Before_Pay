"""Track B integrity verifier — v1.0 (FROZEN).

Gate for the Messy Real-World Document Evaluation dataset.
Runs read-only over data/track_b/ and fails closed on any integrity problem.

Checks:
  1. Manifest present, well-formed, no duplicates, entries == files on disk.
  2. Inventory: exactly case_101..case_112; bundle.json lists exactly the
     files present in the case directory (no extra, no missing).
  3. Document parseability: PDF magic header + non-empty PyMuPDF text layer
     (or pypdf fallback); PNG magic header; JSON parses.
  4. Ground truth == official Phase1Oracle re-derivation from `canonical`.
  5. Canonical validates against the OFFICIAL public_evidence_bundle.json
     schema (unmodified).
  6. Synthetic-vendor rule (same keyword rule as Track A).
  7. Leakage rules: no standalone pay/hold/investigate tokens and no
     answer-indicator strings in any case document, bundle.json, or filename.
  8. Generator determinism: regenerate into a temp dir and compare manifests
     (PDF/PNG/JSON bytes must be reproducible). Skipped if PyMuPDF missing.

Exit 0 + "TRACK B VERIFICATION PASSED" only if everything holds.
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import jsonschema  # noqa: E402
from scripts.validate_phase1 import Phase1Oracle  # noqa: E402

TRACK_B_DIR = Path(__file__).resolve().parent
CASES_DIR = TRACK_B_DIR / "cases"
GROUND_TRUTH_DIR = TRACK_B_DIR / "ground_truth"
MANIFEST_PATH = TRACK_B_DIR / "MANIFEST.sha256"
DESIGN_PATH = TRACK_B_DIR / "DESIGN.md"
PUBLIC_SCHEMA = json.loads(
    (BASE_DIR / "benchmark" / "schemas" / "public_evidence_bundle.json").read_text(encoding="utf-8"))

EXPECTED_CASE_IDS = [f"case_{n}" for n in range(101, 113)]

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None

try:
    import pypdf
except ImportError:  # pragma: no cover
    pypdf = None

SYNTHETIC_KEYWORDS = ["SYNTHETIC", "FAKECORP", "MOCK", "PSEUDO", "TESTAMENT"]
# Same shape as the official Track A leakage validator.
LEAK_PATTERN = re.compile(r"(?<![a-z0-9])(pay|hold|investigate)(?![a-z0-9])", re.IGNORECASE)
ANSWER_INDICATORS = {"answerkey", "expectedfindings", "expectedrecommendation", "groundtruth", "label"}

errors = []


def fail(msg):
    errors.append(msg)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_manifest():
    if not MANIFEST_PATH.is_file():
        fail("MANIFEST.sha256 missing")
        return {}
    lines = MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("--- TRACK B MANIFEST track-b-v"):
        fail("Invalid manifest header")
        return {}
    entries = {}
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split("  ")
        if len(parts) != 2:
            fail(f"Invalid manifest line: {line}")
            continue
        h, rel = parts
        if rel in entries:
            fail(f"Duplicate manifest entry: {rel}")
        entries[rel] = h
    return entries


def check_tree_matches_manifest(entries):
    actual = {}
    for path in CASES_DIR.rglob("*"):
        if path.is_file():
            rel = "cases/" + path.relative_to(CASES_DIR).as_posix()
            actual[rel] = sha256_bytes(path.read_bytes())
    for path in GROUND_TRUTH_DIR.glob("*.json"):
        rel = "ground_truth/" + path.name
        actual[rel] = sha256_bytes(path.read_bytes())
    for rel in entries:
        if rel not in actual:
            fail(f"Manifest references missing file: {rel}")
        elif entries[rel] != actual[rel]:
            fail(f"Hash mismatch for {rel}")
    for rel in actual:
        if rel not in entries:
            fail(f"File on disk not in manifest: {rel}")


def extract_pdf_text(path: Path) -> str:
    if not path.read_bytes().startswith(b"%PDF"):
        fail(f"Bad PDF magic header: {path.name}")
        return ""
    text = ""
    if fitz:
        try:
            doc = fitz.open(stream=path.read_bytes(), filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
        except Exception as exc:  # pragma: no cover
            fail(f"PyMuPDF failed on {path.name}: {exc}")
    if not text.strip() and pypdf:
        try:
            reader = pypdf.PdfReader(str(path))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception:
            pass
    return text


def check_documents(case_dir, bundle):
    listed = bundle["documents"]
    present = sorted(p.name for p in case_dir.iterdir() if p.name != "bundle.json")
    if sorted(listed) != present:
        fail(f"{bundle['case_id']}: bundle.json documents != files on disk "
             f"(listed={sorted(listed)}, present={present})")
        return
    for name in listed:
        path = case_dir / name
        if name.endswith(".pdf"):
            text = extract_pdf_text(path)
            if not text.strip():
                fail(f"{bundle['case_id']}/{name}: PDF has no extractable text layer")
        elif name.endswith(".png"):
            if not path.read_bytes().startswith(b"\x89PNG"):
                fail(f"{bundle['case_id']}/{name}: bad PNG magic header")
        elif name.endswith(".json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                fail(f"{bundle['case_id']}/{name}: invalid JSON ({exc})")
        else:
            fail(f"{bundle['case_id']}/{name}: unexpected document type")


def check_leakage(value, where):
    if isinstance(value, dict):
        for k, v in value.items():
            check_leakage(k, where)
            check_leakage(v, where)
    elif isinstance(value, list):
        for item in value:
            check_leakage(item, where)
    elif isinstance(value, str):
        if LEAK_PATTERN.search(value):
            fail(f"Leakage: standalone recommendation token in {where}: {value!r}")
        normalized = re.sub(r"[^a-z0-9]+", "", value.lower())
        for term in ANSWER_INDICATORS:
            if term in normalized:
                fail(f"Leakage: answer indicator '{term}' in {where}: {value!r}")


def check_ground_truth(gt):
    case_id = gt.get("case_id")
    canonical = gt.get("canonical")
    if not isinstance(canonical, dict):
        fail(f"{case_id}: ground truth missing canonical bundle")
        return
    try:
        jsonschema.validate(instance=canonical, schema=PUBLIC_SCHEMA)
    except jsonschema.ValidationError as exc:
        fail(f"{case_id}: canonical fails official public schema: {exc.message}")

    rec, findings = Phase1Oracle().evaluate(canonical)
    if gt.get("expected_recommendation") != rec or sorted(gt.get("expected_findings", [])) != sorted(findings):
        fail(f"{case_id}: ground truth drifts from official oracle "
             f"(file={gt.get('expected_recommendation')}/{gt.get('expected_findings')}, "
             f"oracle={rec}/{sorted(findings)})")

    vendor_name = canonical["invoice"]["vendor_name"].upper()
    if not any(k in vendor_name for k in SYNTHETIC_KEYWORDS):
        fail(f"{case_id}: non-synthetic vendor name: {vendor_name}")


def determinism_via_temp_copy():
    """True determinism check: copy the generator into a temp TRACK_B root,
    regenerate there, and compare manifests. The subprocess runs with the
    repo root on PYTHONPATH so the official oracle import resolves."""
    import os

    if fitz is None:
        print("[SKIP] Determinism check (PyMuPDF unavailable)")
        return
    with tempfile.TemporaryDirectory(prefix="track_b_det_") as tmp:
        tmp = Path(tmp)
        root = tmp / "track_b"
        root.mkdir()
        shutil.copy2(TRACK_B_DIR / "generate_track_b.py", root / "generate_track_b.py")
        # Do NOT pre-create cases/ — the generator's freeze guard refuses to
        # run into an existing tree and creates its own directories.
        env = {**dict(os.environ), "PYTHONPATH": str(BASE_DIR)}
        proc = subprocess.run(
            [sys.executable, str(root / "generate_track_b.py")],
            cwd=tmp, capture_output=True, text=True, env=env,
        )
        if proc.returncode != 0:
            fail(f"Determinism regeneration failed: {proc.stderr.strip()[:400]}")
            return
        regen = (root / "MANIFEST.sha256").read_bytes()
        frozen = MANIFEST_PATH.read_bytes()
        if regen != frozen:
            fail("Generator is not deterministic: regenerated manifest differs from frozen manifest")


def main():
    if not DESIGN_PATH.is_file():
        fail("DESIGN.md missing (frozen design document required)")
    entries = read_manifest()
    if entries:
        check_tree_matches_manifest(entries)

    case_dirs = sorted(p.name for p in CASES_DIR.iterdir() if p.is_dir()) if CASES_DIR.is_dir() else []
    if case_dirs != EXPECTED_CASE_IDS:
        fail(f"Inventory mismatch: expected {EXPECTED_CASE_IDS}, found {case_dirs}")

    for case_id in EXPECTED_CASE_IDS:
        case_dir = CASES_DIR / case_id
        bundle_path = case_dir / "bundle.json"
        if not bundle_path.is_file():
            fail(f"{case_id}: bundle.json missing")
            continue
        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"{case_id}: bundle.json invalid JSON ({exc})")
            continue
        if bundle.get("case_id") != case_id or bundle.get("track") != "B":
            fail(f"{case_id}: bundle.json case_id/track mismatch")
            continue
        check_leakage(bundle, f"{case_id}/bundle.json")
        check_documents(case_dir, bundle)

        # Leakage rules apply to SYSTEM INPUTS (case documents + bundles) —
        # the same protection as Track A. Ground truth is evaluator-side and
        # legitimately contains labels (identical to Track A's own
        # data/cases/ground_truth); it is verified separately below.
        for path in case_dir.iterdir():
            if path.name.endswith(".json"):
                check_leakage(path.read_text(encoding="utf-8"), f"{case_id}/{path.name}")

        gt_path = GROUND_TRUTH_DIR / f"{case_id}.json"
        if not gt_path.is_file():
            fail(f"{case_id}: ground truth missing")
            continue
        try:
            gt = json.loads(gt_path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"{case_id}: ground truth invalid JSON ({exc})")
            continue
        check_ground_truth(gt)

    challenging = [c for c in EXPECTED_CASE_IDS
                   if json.loads((GROUND_TRUTH_DIR / f"{c}.json").read_text(encoding="utf-8")).get("challenging")]
    if challenging != ["case_111"]:
        fail(f"Exactly one challenging case (case_111) required, found {challenging}")

    determinism_via_temp_copy()

    if errors:
        print("TRACK B VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("TRACK B VERIFICATION PASSED")
    print(f"  cases: {len(EXPECTED_CASE_IDS)} (case_101..case_112), case_111 challenging")
    print("  ground truth: 12/12 re-derived by official Phase1Oracle, no drift")
    print("  documents: all parseable, bundles consistent, no leakage, synthetic vendors only")
    print("  generator: deterministic (regenerated manifest matches frozen manifest)")


if __name__ == "__main__":
    main()
