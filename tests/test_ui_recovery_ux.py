import os
import sys
import json
import threading
import time
import urllib.request
import unittest
from http.server import HTTPServer
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ui.server import ReviewerAppHandler
from src.agent.credentials import CredentialManager, Credential, CredentialState, RetrySignal
from src.agent.orchestrator import AgentOrchestrator

class TestUIRecoveryUX(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8891
        cls.server = HTTPServer(("127.0.0.1", cls.port), ReviewerAppHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, endpoint, data):
        url = f"http://127.0.0.1:{self.port}{endpoint}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_ui_recovery_elements_in_html(self):
        index_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'ui', 'static', 'index.html')
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("recovery-notice", content)
        self.assertIn("recovery-slots-grid", content)
        self.assertIn("Connection Rate-Limit Failover", content)
        self.assertIn("All Provider Connections Exhausted", content)

    def test_ui_recovery_info_in_api_response(self):
        status, res = self._post("/api/investigate", {"case_id": "case_001"})
        self.assertEqual(status, 200)
        self.assertIn("recovery_info", res)
        rec_info = res["recovery_info"]
        self.assertIn("failover_occurred", rec_info)
        self.assertIn("pool_exhausted", rec_info)
        self.assertIn("slots", rec_info)
        self.assertTrue(len(rec_info["slots"]) >= 1)

    def test_ui_recovery_pool_exhaustion_fail_closed(self):
        # Ensure test case is uncached
        test_cache = "data/cache/extractions/case_987.json"
        if os.path.exists(test_cache):
            os.remove(test_cache)

        # Create orchestrator with all credentials exhausted
        cm = CredentialManager(explicit_keys=["key_exhausted_1", "key_exhausted_2"])
        for c in cm.credentials:
            c.state = CredentialState.EXHAUSTED
            
        orch = AgentOrchestrator(credential_manager=cm)
        with patch.object(ReviewerAppHandler, 'get_orchestrator', return_value=orch):
            status, res = self._post("/api/investigate", {"case_id": "case_987", "raw_evidence": "{\"invoice\": {\"total\": 100}}"})
            self.assertEqual(status, 200)
            self.assertEqual(res["result"]["recommendation"], "INVESTIGATE")
            self.assertIn("All credentials exhausted", res["result"]["findings"])
            self.assertTrue(res["recovery_info"]["pool_exhausted"])
            self.assertEqual(res["result"]["findings"], ["All credentials exhausted"])
            
        if os.path.exists(test_cache):
            os.remove(test_cache)

if __name__ == '__main__':
    unittest.main()
