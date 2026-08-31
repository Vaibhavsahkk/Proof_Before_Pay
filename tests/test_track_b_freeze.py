"""Track B freeze tests (Sub-Phase A1).

Wraps data/track_b/verify_track_b.py checks for the standard test suite.
PyMuPDF-dependent parts (PDF parseability, generator determinism, PDF-heavy
document checks) are skipped when PyMuPDF is unavailable — e.g. inside the
current Docker verifier image — but manifest, ground-truth, schema,
inventory, bundle-consistency, and leakage checks always run.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
TRACK_B = BASE_DIR / "data" / "track_b"
CASES_DIR = TRACK_B / "cases"
GROUND_TRUTH_DIR = TRACK_B / "ground_truth"
MANIFEST_PATH = TRACK_B / "MANIFEST.sha256"
DESIGN_PATH = TRACK_B / "DESIGN.md"

EXPECTED_CASE_IDS = [f"case_{n}" for n in range(101, 113)]

sys.path.insert(0, str(BASE_DIR))

fitz = pytest.importorskip("scripts.validate_phase1", reason="official oracle required").Phase1Oracle  # noqa: F401

try:
    import fitz as pymupdf  # noqa: E402
except ImportError:  # pragma: no cover
    pymupdf = None


def _read_manifest():
    lines = MANIFEST_PATH.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("--- TRACK B MANIFEST track-b-v")
    return {line.split("  ")[1]: line.split("  ")[0] for line in lines[1:] if line.strip()}


def test_design_doc_frozen_and_declares_version():
    content = DESIGN_PATH.read_text(encoding="utf-8")
    assert "FROZEN" in content
    assert "v1.0" in content
    assert "case_111" in content  # challenging case declared


def test_manifest_exists_and_lists_all_73_entries():
    entries = _read_manifest()
    case_files = [p for p in CASES_DIR.rglob("*") if p.is_file()]
    gt_files = list(GROUND_TRUTH_DIR.glob("*.json"))
    assert len(entries) == len(case_files) + len(gt_files)
    assert len(entries) >= 60


def test_inventory_is_exactly_case_101_to_112():
    assert sorted(p.name for p in CASES_DIR.iterdir()) == EXPECTED_CASE_IDS


def test_every_case_bundle_matches_files_on_disk():
    for case_id in EXPECTED_CASE_IDS:
        case_dir = CASES_DIR / case_id
        bundle = json.loads((case_dir / "bundle.json").read_text(encoding="utf-8"))
        assert bundle["case_id"] == case_id
        assert bundle["track"] == "B"
        listed = sorted(bundle["documents"])
        present = sorted(p.name for p in case_dir.iterdir() if p.name != "bundle.json")
        assert listed == present, f"{case_id}: bundle/files mismatch"


def test_ground_truth_rederived_by_official_oracle():
    """The core anti-targeting guarantee: no hand-authored labels."""
    from scripts.validate_phase1 import Phase1Oracle
    oracle = Phase1Oracle()
    for case_id in EXPECTED_CASE_IDS:
        gt = json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        rec, findings = oracle.evaluate(gt["canonical"])
        assert gt["expected_recommendation"] == rec, f"{case_id} recommendation drift"
        assert sorted(gt["expected_findings"]) == sorted(findings), f"{case_id} findings drift"
        assert gt["derived_by"].startswith("scripts/validate_phase1.Phase1Oracle")


def test_canonical_bundles_validate_against_official_schema():
    import jsonschema
    schema = json.loads(
        (BASE_DIR / "benchmark" / "schemas" / "public_evidence_bundle.json").read_text(encoding="utf-8"))
    for case_id in EXPECTED_CASE_IDS:
        gt = json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        jsonschema.validate(instance=gt["canonical"], schema=schema)


def test_label_distribution_uses_predeclared_taxonomy():
    from collections import Counter
    labels = Counter()
    for case_id in EXPECTED_CASE_IDS:
        gt = json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        labels[gt["expected_recommendation"]] += 1
    assert labels == {"PAY": 2, "HOLD": 6, "INVESTIGATE": 4}


def test_exactly_one_challenging_case_111():
    challenging = []
    for case_id in EXPECTED_CASE_IDS:
        gt = json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        if gt.get("challenging"):
            challenging.append(case_id)
    assert challenging == ["case_111"]
    gt111 = json.loads((GROUND_TRUTH_DIR / "case_111.json").read_text(encoding="utf-8"))
    assert gt111["expected_findings"] == ["Duplicate Billing", "Unverified Bank Change"]


def test_no_leakage_in_case_documents_or_bundles():
    pattern = re.compile(r"(?<![a-z0-9])(pay|hold|investigate)(?![a-z0-9])", re.IGNORECASE)
    indicators = {"answerkey", "expectedfindings", "expectedrecommendation", "groundtruth", "label"}

    def scan(value, where, problems):
        if isinstance(value, dict):
            for k, v in value.items():
                scan(k, where, problems)
                scan(v, where, problems)
        elif isinstance(value, list):
            for item in value:
                scan(item, where, problems)
        elif isinstance(value, str):
            if pattern.search(value):
                problems.append(f"token in {where}: {value!r}")
            norm = re.sub(r"[^a-z0-9]+", "", value.lower())
            for term in indicators:
                if term in norm:
                    problems.append(f"indicator in {where}: {value!r}")

    problems = []
    for case_id in EXPECTED_CASE_IDS:
        for path in (CASES_DIR / case_id).iterdir():
            if path.name.endswith((".json",)):
                scan(json.loads(path.read_text(encoding="utf-8")), f"{case_id}/{path.name}", problems)
    assert not problems, problems


def test_vendor_names_are_synthetic():
    keywords = ["SYNTHETIC", "FAKECORP", "MOCK", "PSEUDO", "TESTAMENT"]
    for case_id in EXPECTED_CASE_IDS:
        gt = json.loads((GROUND_TRUTH_DIR / f"{case_id}.json").read_text(encoding="utf-8"))
        vendor = gt["canonical"]["invoice"]["vendor_name"].upper()
        assert any(k in vendor for k in keywords), f"{case_id}: {vendor}"


def test_document_format_mix_covers_pdf_png_and_json():
    seen = {"pdf": 0, "png": 0, "json": 0}
    for case_id in EXPECTED_CASE_IDS:
        for path in (CASES_DIR / case_id).iterdir():
            if path.name.endswith(".pdf"):
                seen["pdf"] += 1
            elif path.name.endswith(".png"):
                seen["png"] += 1
            elif path.name.endswith(".json") and path.name != "bundle.json":
                seen["json"] += 1
    assert seen["pdf"] >= 10 and seen["png"] >= 2 and seen["json"] >= 2, seen


@pytest.mark.skipif(pymupdf is None, reason="PyMuPDF not installed")
def test_every_pdf_has_extractable_text_layer():
    for case_id in EXPECTED_CASE_IDS:
        for path in (CASES_DIR / case_id).glob("*.pdf"):
            data = path.read_bytes()
            assert data.startswith(b"%PDF"), f"{path.name}: bad magic header"
            doc = pymupdf.open(stream=data, filetype="pdf")
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            assert text.strip(), f"{path.name}: no text layer"


@pytest.mark.skipif(pymupdf is None, reason="PyMuPDF not installed")
def test_png_documents_have_valid_magic():
    for case_id in EXPECTED_CASE_IDS:
        for path in (CASES_DIR / case_id).glob("*.png"):
            assert path.read_bytes().startswith(b"\x89PNG"), f"{path.name}: bad PNG"


def test_full_verifier_passes():
    """Run the real integrity gate end-to-end (not a re-implementation)."""
    proc = subprocess.run(
        [sys.executable, str(TRACK_B / "verify_track_b.py")],
        capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "TRACK B VERIFICATION PASSED" in proc.stdout
