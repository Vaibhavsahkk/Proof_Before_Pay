import os
import sys
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ui.server import ReviewerAppHandler
from src.agent.orchestrator import AgentOrchestrator

class TestReviewerUI(unittest.TestCase):
    def setUp(self):
        self.static_index_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'static', 'index.html')

    def test_ui_static_index_exists_and_has_core_elements(self):
        self.assertTrue(os.path.exists(self.static_index_path))
        with open(self.static_index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check core UX & design elements
        self.assertIn("Proof Before Pay", content)
        self.assertIn("Review Supplier Payment", content)
        self.assertIn("drop-zone", content)
        self.assertIn("case_001", content)
        self.assertIn("rec-banner", content)
        self.assertIn("What should you do next?", content)
        self.assertIn("Automated Verification Checks", content)
        self.assertIn("Detailed System Audit Trail", content)
        self.assertIn("prefers-reduced-motion", content)

    def test_ui_investigate_pipeline_pay(self):
        orch = AgentOrchestrator()
        case_file = "data/cases/public/case_001.json"
        with open(case_file, "r", encoding="utf-8") as f:
            raw_evidence = f.read()
            
        result = orch.run_workflow("case_001", raw_evidence)
        self.assertEqual(result["recommendation"], "PAY")
        self.assertEqual(result["findings"], [])
        self.assertIn("invoice", result["evidence_references"])

    def test_ui_investigate_pipeline_hold(self):
        orch = AgentOrchestrator()
        case_file = "data/cases/public/case_002.json"
        with open(case_file, "r", encoding="utf-8") as f:
            raw_evidence = f.read()
            
        result = orch.run_workflow("case_002", raw_evidence)
        self.assertEqual(result["recommendation"], "HOLD")
        self.assertIn("Duplicate Billing", result["findings"])

    def test_ui_investigate_pipeline_investigate(self):
        orch = AgentOrchestrator()
        case_file = "data/cases/public/case_005.json"
        with open(case_file, "r", encoding="utf-8") as f:
            raw_evidence = f.read()
            
        result = orch.run_workflow("case_005", raw_evidence)
        self.assertEqual(result["recommendation"], "INVESTIGATE")
        self.assertIn("Unverified Bank Change", result["findings"])

    def test_ui_investigate_missing_evidence(self):
        orch = AgentOrchestrator()
        case_file = "data/cases/public/case_011.json" # Missing Vendor Master
        with open(case_file, "r", encoding="utf-8") as f:
            raw_evidence = f.read()
            
        result = orch.run_workflow("case_011", raw_evidence)
        self.assertEqual(result["recommendation"], "INVESTIGATE")
        self.assertIn("Missing Vendor Master", result["findings"])

    def test_ui_investigate_malformed_input(self):
        orch = AgentOrchestrator()
        result = orch.run_workflow("case_malformed", "Not a valid json {broken:")
        self.assertEqual(result["recommendation"], "INVESTIGATE")
        self.assertIn("Extraction or System Failure", result["findings"])

if __name__ == '__main__':
    unittest.main()
