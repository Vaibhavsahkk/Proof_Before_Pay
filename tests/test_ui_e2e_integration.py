import os
import sys
import json
import base64
import threading
import time
import urllib.request
import urllib.error
import unittest
from http.server import HTTPServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ui.server import ReviewerAppHandler

class TestUIEndToEndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8899
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

    def _get(self, endpoint):
        url = f"http://127.0.0.1:{self.port}{endpoint}"
        with urllib.request.urlopen(url) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_e2e_flow_case_001_pay(self):
        status, res = self._post("/api/investigate", {"case_id": "case_001"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "PAY")
        self.assertEqual(res["result"]["findings"], [])
        self.assertTrue(len(res["result"]["evidence_references"]) >= 4)
        self.assertTrue(os.path.exists(res["trace_file"]))

    def test_e2e_flow_case_002_hold_duplicate(self):
        status, res = self._post("/api/investigate", {"case_id": "case_002"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "HOLD")
        self.assertIn("Duplicate Billing", res["result"]["findings"])

    def test_e2e_flow_case_005_investigate_bank_change(self):
        status, res = self._post("/api/investigate", {"case_id": "case_005"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "INVESTIGATE")
        self.assertIn("Unverified Bank Change", res["result"]["findings"])

    def test_e2e_flow_case_011_missing_vendor_master(self):
        status, res = self._post("/api/investigate", {"case_id": "case_011"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "INVESTIGATE")
        self.assertIn("Missing Vendor Master", res["result"]["findings"])

    def test_e2e_flow_case_006_multiple_findings(self):
        status, res = self._post("/api/investigate", {"case_id": "case_006"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "HOLD")
        self.assertTrue(len(res["result"]["findings"]) >= 2)

    def test_e2e_flow_case_007_math_error(self):
        status, res = self._post("/api/investigate", {"case_id": "case_007"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "HOLD")
        self.assertIn("Math Error", res["result"]["findings"])

    def test_e2e_flow_case_008_currency_mismatch(self):
        status, res = self._post("/api/investigate", {"case_id": "case_008"})
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "HOLD")
        self.assertIn("Currency Mismatch", res["result"]["findings"])

    def test_e2e_failure_flow_malformed_json_syntax(self):
        url = f"http://127.0.0.1:{self.port}/api/investigate"
        req = urllib.request.Request(url, data=b"{malformed_json_not_valid", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Should have failed with 400 Bad Request")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("Invalid JSON payload", err_data["error"])

    def test_e2e_failure_flow_missing_case_id(self):
        url = f"http://127.0.0.1:{self.port}/api/investigate"
        req = urllib.request.Request(url, data=json.dumps({"case_id": "non_existent_case_9999"}).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Should have failed with 400 Bad Request")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("not found", err_data["error"])

    def test_e2e_trace_retrieval(self):
        status, res = self._post("/api/investigate", {"case_id": "case_001"})
        trace_file = res["trace_file"]
        status_trace, trace_data = self._get(f"/api/trace?file={urllib.parse.quote(trace_file)}")
        self.assertEqual(status_trace, 200)
        self.assertTrue(len(trace_data["events"]) > 0)
        phases = [e["phase"] for e in trace_data["events"]]
        self.assertIn("extract", phases)
        self.assertIn("verify", phases)
        self.assertIn("apply_rules", phases)

    def test_e2e_flow_uploaded_json_bundle(self):
        with open("data/cases/public/case_001.json", "r", encoding="utf-8") as f:
            case_data = f.read()
        b64_data = base64.b64encode(case_data.encode("utf-8")).decode("utf-8")
        status, res = self._post("/api/investigate", {
            "case_id": "uploaded_case_001",
            "files": [{"name": "evidence.json", "data": b64_data, "type": "application/json"}]
        })
        self.assertEqual(status, 200)
        self.assertEqual(res["result"]["recommendation"], "PAY")
        self.assertIn("uploaded_documents_metadata", res)
        self.assertEqual(len(res["uploaded_documents_metadata"]), 1)

    def test_e2e_flow_uploaded_multi_documents(self):
        with open("data/cases/public/case_001.json", "r", encoding="utf-8") as f:
            case_data = json.load(f)
        
        inv_json = json.dumps({"invoice": case_data["invoice"]})
        po_json = json.dumps({"purchase_order": case_data["purchase_order"], "goods_receipt": case_data["goods_receipt"], "vendor_master": case_data["vendor_master"]})
        
        status, res = self._post("/api/investigate", {
            "case_id": "multi_doc_bundle",
            "files": [
                {"name": "invoice_doc.json", "data": base64.b64encode(inv_json.encode()).decode(), "type": "application/json"},
                {"name": "supporting_orders.json", "data": base64.b64encode(po_json.encode()).decode(), "type": "application/json"}
            ]
        })
        self.assertEqual(status, 200)
        self.assertIn("uploaded_documents_metadata", res)
        self.assertEqual(len(res["uploaded_documents_metadata"]), 2)

    def test_e2e_flow_uploaded_corrupted_document(self):
        url = f"http://127.0.0.1:{self.port}/api/investigate"
        bad_payload = json.dumps({
            "case_id": "bad_doc_case",
            "files": [{"name": "corrupted.pdf", "data": base64.b64encode(b"NOT_A_PDF").decode(), "type": "application/pdf"}]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=bad_payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                self.fail("Should have failed with 400 Bad Request")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)
            err_data = json.loads(e.read().decode("utf-8"))
            self.assertIn("missing PDF magic header", err_data["error"])
            self.assertEqual(err_data["result"]["recommendation"], "INVESTIGATE")
            self.assertIn("Unreadable Document", err_data["result"]["findings"])

if __name__ == '__main__':
    unittest.main()
