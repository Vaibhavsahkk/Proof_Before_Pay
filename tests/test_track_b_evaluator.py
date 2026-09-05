import json
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
EVALUATOR = BASE_DIR / "data" / "track_b" / "evaluation" / "evaluate_track_b.py"


def test_case_112_cascade_is_reported_and_inclusion_is_scored(tmp_path):
    output = tmp_path / "results.json"
    proc = subprocess.run(
        [sys.executable, str(EVALUATOR),
         "--baseline-run", "frozen_v2_assembly",
         "--agent-run", "frozen_v1_assembly",
         "--out", str(output)],
        cwd=BASE_DIR, capture_output=True, text=True, check=True,
    )
    result = json.loads(output.read_text(encoding="utf-8"))
    case = next(item for item in result["agent"]["per_case"] if item["case_id"] == "case_112")

    assert case["findings_correct"] is False
    assert case["findings_included"] is True
    assert case["missing_findings"] == []
    assert case["cascade_findings"] == ["Math Error"]
    assert result["agent"]["metrics"]["findings_inclusion_percent"] > result["agent"]["metrics"]["findings_exactness_percent"]
    assert "agent cascade findings" in proc.stdout