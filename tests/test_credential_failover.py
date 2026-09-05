import sys
import os
import time
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.credentials import CredentialManager, CredentialState, RetrySignal
from src.agent.orchestrator import AgentOrchestrator
from src.agent.extraction import LLMExtractor

class TestCredentialFailover(unittest.TestCase):
    def setUp(self):
        # Ensure clean state
        os.environ["GEMINI_API_KEYS"] = "valid_key_one_long_enough_1,valid_key_two_long_enough_2,valid_key_three_long_enough_3"
        if os.path.exists("data/cache/extractions/case_429.json"):
            os.remove("data/cache/extractions/case_429.json")
        if os.path.exists("data/cache/explanations/case_429.json"):
            os.remove("data/cache/explanations/case_429.json")
            
    def tearDown(self):
        if os.path.exists("data/cache/extractions/case_429.json"):
            os.remove("data/cache/extractions/case_429.json")
        if os.path.exists("data/cache/explanations/case_429.json"):
            os.remove("data/cache/explanations/case_429.json")

    @patch("src.agent.credentials.os.path.exists")
    def test_credential_loading(self, mock_exists):
        mock_exists.return_value = False
        cm = CredentialManager(explicit_keys=["exp1", "exp2"])
        self.assertEqual(len(cm.credentials), 2)
        self.assertEqual(cm.credentials[0].api_key, "exp1")
        
        cm_env = CredentialManager()
        self.assertEqual(len(cm_env.credentials), 3)
        self.assertEqual(cm_env.credentials[0].api_key, "valid_key_one_long_enough_1")

    @patch("src.agent.credentials.time.time")
    def test_cooldown_and_exhaustion(self, mock_time):
        mock_time.return_value = 100.0
        cm = CredentialManager(["k1", "k2"])
        
        self.assertEqual(cm.get_current_key(), "k1")
        cm.mark_cooldown(60) # k1 cooldown until 160
        self.assertEqual(cm.credentials[0].state, CredentialState.COOLDOWN)
        
        self.assertEqual(cm.get_current_key(), "k2")
        cm.mark_exhausted("Quota") # k2 exhausted
        self.assertEqual(cm.credentials[1].state, CredentialState.EXHAUSTED)
        
        # Now both are unavailable
        with self.assertRaises(RetrySignal):
            cm.get_current_key()
            
        self.assertEqual(cm.get_wait_time(), 60.0)
        
        # Advance time
        mock_time.return_value = 161.0
        self.assertEqual(cm.get_current_key(), "k1") # K1 recovered
        self.assertEqual(cm.credentials[0].state, CredentialState.ACTIVE)

    @patch("src.agent.extraction.genai.Client")
    def test_orchestrator_resume_state(self, MockClient):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        
        mock_models = MagicMock()
        mock_client.models = mock_models
        
        call_count = [0]
        
        def fake_generate_content(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First try fails with 429
                raise Exception("429 RESOURCE_EXHAUSTED")
            
            # Second try succeeds
            mock_resp = MagicMock()
            # Must return valid structure, even if mocked. The response must
            # ALSO satisfy the item/totals field contract (invoice-level
            # subtotal/tax/total + items with quantity/unit_price/line_total),
            # otherwise the extractor's contract validation fires a
            # reinforced retry and this test would count 4 calls instead of 3.
            if kwargs.get('contents', '').startswith("You are a financial investigator"):
                 mock_resp.text = json.dumps({"uncertainty": "test", "required_human_next_step": "test"})
            else:
                 mock_resp.text = json.dumps({
                     "case_id": "case_429",
                     "invoice": {
                         "invoice_number": "INV-429",
                         "vendor_name": "SYNTHETIC TEST VENDOR",
                         "vendor_tax_id": "TX-429",
                         "bank_account": "ACC-429",
                         "currency": "USD",
                         "tax_rate_percent": "0.00",
                         "items": [{
                             "item_id": "TEST-1",
                             "description": "test item",
                             "quantity": "1",
                             "unit_price": "100.00",
                             "line_total": "100.00"
                         }],
                         "subtotal": "100.00",
                         "tax": "0.00",
                         "total": "100.00"
                     }
                 })
            return mock_resp
            
        mock_models.generate_content.side_effect = fake_generate_content
        
        # Set explicitly to 2 keys
        orchestrator = AgentOrchestrator(api_key="keyA,keyB")
        
        raw_evidence = '{"test": "data"}'
        result = orchestrator.run_workflow("case_429", raw_evidence)
        
        self.assertEqual(result["case_id"], "case_429")
        # 1st call fails, 2nd succeeds extraction, 3rd succeeds explanation
        self.assertEqual(call_count[0], 3)
        self.assertEqual(orchestrator.extractor.cred_manager.current_index, 1)

if __name__ == '__main__':
    unittest.main()
