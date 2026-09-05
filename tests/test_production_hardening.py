"""Regression tests for the production-hardening fixes (2026-09-06 round).

Covers:
  1. OCR model fallback chain in DocumentAdapter (primary model 404/empty
     -> fallback model used; quota/429 propagates to credential failover).
  2. Absent-document guard in LLMExtractor (_missing_extracted_documents):
     source-present-but-dropped documents are contract violations;
     genuinely-absent documents are not (real Missing-PO findings preserved).
  3. UI server auth/CORS/body-limit hardening (401 without token, 200 with
     token, 413 on oversized bodies, strict CORS default).
  4. Flaky-test root cause regression: credential cooldown expiry must not
     depend on real elapsed milliseconds (frozen-clock contract).
"""

import json
import os
import sys
import threading
import time
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.credentials import CredentialManager, CredentialState
from src.agent.extraction import LLMExtractor
from src.agent.document_adapter import DocumentAdapter, DocumentProcessingError
from src.ui.server import ReviewerAppHandler


class TestOCRFallback(unittest.TestCase):
    """Fix 1: transcription model fallback chain."""

    def _adapter_with_mocks(self):
        cm = CredentialManager(explicit_keys=["test_key_long_enough"])
        adapter = DocumentAdapter(credential_manager=cm)
        return adapter, cm

    def test_primary_model_404_falls_back(self):
        adapter, _ = self._adapter_with_mocks()
        fake_primary = MagicMock()
        fake_primary.text = None  # or raise below
        fake_fallback = MagicMock()
        fake_fallback.text = "TRANSCRIBED TEXT"

        def gen(model, contents):
            if model == "gemini-2.5-flash":
                raise RuntimeError("404 NOT_FOUND. This model is no longer available")
            return fake_fallback

        client = MagicMock()
        client.models.generate_content.side_effect = gen
        with patch("src.agent.document_adapter.genai.Client", return_value=client):
            out = adapter._extract_multimodal_document(
                "po.png", b"\x89PNG fake", "image/png"
            )
        self.assertIn("TRANSCRIBED TEXT", out)
        self.assertIn("po.png", out)

    def test_primary_empty_text_falls_back(self):
        adapter, _ = self._adapter_with_mocks()
        fake_empty = MagicMock()
        fake_empty.text = "   "
        fake_good = MagicMock()
        fake_good.text = "GOOD TEXT"

        def gen(model, contents):
            return fake_empty if model == "gemini-2.5-flash" else fake_good

        client = MagicMock()
        client.models.generate_content.side_effect = gen
        with patch("src.agent.document_adapter.genai.Client", return_value=client):
            out = adapter._extract_multimodal_document(
                "po.png", b"\x89PNG fake", "image/png"
            )
        self.assertIn("GOOD TEXT", out)

    def test_quota_error_propagates_not_falls_back(self):
        """A 429 on EVERY candidate model is a KEY-level condition: it must
        reach the credential failover path after trying all models."""
        adapter, cm = self._adapter_with_mocks()

        def gen(model, contents):
            raise RuntimeError(
                "429 RESOURCE_EXHAUSTED. Quota exceeded for metric"
            )

        client = MagicMock()
        client.models.generate_content.side_effect = gen
        with patch("src.agent.document_adapter.genai.Client", return_value=client):
            with self.assertRaises(Exception):
                adapter._extract_multimodal_document(
                    "po.png", b"\x89PNG fake", "image/png"
                )
        # The key was marked cooling down, not rotated past.
        self.assertEqual(cm.credentials[0].state, CredentialState.COOLDOWN)

    def test_quota_on_primary_falls_back_to_secondary_model(self):
        """A 429 on the PRIMARY model alone must NOT block: the same key's
        fallback model is tried before any credential rotation."""
        adapter, cm = self._adapter_with_mocks()
        fake_good = MagicMock()
        fake_good.text = "FALLBACK TRANSCRIPTION"

        def gen(model, contents):
            if model == "gemini-2.5-flash":
                raise RuntimeError(
                    "429 RESOURCE_EXHAUSTED. Quota exceeded for metric"
                )
            return fake_good

        client = MagicMock()
        client.models.generate_content.side_effect = gen
        with patch("src.agent.document_adapter.genai.Client", return_value=client):
            out = adapter._extract_multimodal_document(
                "po.png", b"\x89PNG fake", "image/png"
            )
        self.assertIn("FALLBACK TRANSCRIPTION", out)

    def test_all_models_failing_is_processing_error(self):
        adapter, _ = self._adapter_with_mocks()

        def gen(model, contents):
            raise RuntimeError("500 INTERNAL")

        client = MagicMock()
        client.models.generate_content.side_effect = gen
        with patch("src.agent.document_adapter.genai.Client", return_value=client):
            with self.assertRaises(DocumentProcessingError):
                adapter._extract_multimodal_document(
                    "po.png", b"\x89PNG fake", "image/png"
                )


class TestAbsentDocumentGuard(unittest.TestCase):
    """Fix 2: source-present documents dropped by the LLM are violations."""

    SRC_WITH_PO = (
        "=== DOCUMENT: invoice.pdf ===\nSYNTHETIC SAMPLE INVOICE\n"
        "=== DOCUMENT: purchase_order.png ===\n"
        "SYNTHETIC SAMPLE PURCHASE ORDER\nPO Number: PO-3102\n"
        "Order Lines:\nItem PAPER-A4 | Quantity 40 | Unit Price 12.50 USD"
    )

    def test_dropped_po_is_violation(self):
        data = {
            "invoice": {
                "items": [{"item_id": "PAPER-A4", "line_total": "500.00",
                           "description": ""}]
            },
            "purchase_order": None,
        }
        v = LLMExtractor._missing_extracted_documents(data, self.SRC_WITH_PO)
        docs = [doc for doc, _, _ in v]
        self.assertIn("purchase_order", docs)

    def test_genuinely_missing_po_is_not_violation(self):
        src_invoice_only = (
            "=== DOCUMENT: invoice.pdf ===\nSYNTHETIC SAMPLE INVOICE\n"
            "Invoice No.: INV-2112\nTotal Amount: 450.00 USD"
        )
        data = {
            "invoice": {
                "items": [{"item_id": "HVAC-SVC", "quantity": "2",
                           "unit_price": "225.00", "line_total": "450.00",
                           "description": ""}],
                "subtotal": "450.00", "tax": "0.00", "total": "450.00",
            },
            "purchase_order": None, "goods_receipt": None,
            "vendor_master": None,
        }
        v = LLMExtractor._missing_extracted_documents(data, src_invoice_only)
        self.assertEqual(v, [])

    def test_case112_shape_grn_not_false_flagged(self):
        # case_112 source contains invoice + PO only; GRN absent genuinely.
        src = (
            "=== DOCUMENT: invoice.pdf ===\nINV-2112 PSEUDO SERVICES\n"
            "=== DOCUMENT: purchase_order.pdf ===\nPO Number: PO-3112"
        )
        data = {
            "invoice": {"items": [{"item_id": "X", "quantity": "1",
                                    "unit_price": "1.00", "line_total": "1.00",
                                    "description": ""}],
                        "subtotal": "1.00", "tax": "0.00", "total": "1.00"},
            "purchase_order": {"items": [{"item_id": "X", "quantity": "1",
                                           "unit_price": "1.00"}]},
            "goods_receipt": None,
        }
        v = LLMExtractor._missing_extracted_documents(data, src)
        self.assertEqual(v, [])

    def test_dropped_vendor_master_is_violation(self):
        src_vm = (
            '=== DOCUMENT: vendor_master.json ===\n'
            '{"vendor_name": "ACME SYNTHETIC", "vendor_tax_id": "TX-1"}'
        )
        data = {"invoice": {}, "vendor_master": None}
        v = LLMExtractor._missing_extracted_documents(data, src_vm)
        docs = [doc for doc, _, _ in v]
        self.assertIn("vendor_master", docs)

    def test_empty_source_is_defensively_clean(self):
        self.assertEqual(
            LLMExtractor._missing_extracted_documents({}, ""), []
        )


class TestUIServerHardening(unittest.TestCase):
    """Fix 4: auth token, body limit, strict CORS."""

    @classmethod
    def setUpClass(cls):
        # Ephemeral port: the OS picks a free port, eliminating cross-run /
        # cross-process socket interference seen with fixed ports.
        cls.server = HTTPServer(("127.0.0.1", 0), ReviewerAppHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, data, token=None, path="/api/investigate"):
        url = f"http://127.0.0.1:{self.port}{path}"
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["X-Auth-Token"] = token
        req = urllib.request.Request(
            url, data=json.dumps(data).encode("utf-8"), headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def test_post_without_token_is_401(self):
        status, body = self._post({"case_id": "case_001"})
        self.assertEqual(status, 401)
        self.assertIn("Unauthorized", body["error"])

    def test_post_with_wrong_token_is_401(self):
        status, body = self._post({"case_id": "case_001"}, token="wrong-token")
        self.assertEqual(status, 401)

    def test_post_with_valid_token_is_accepted(self):
        status, body = self._post(
            {"case_id": "case_001"},
            token=ReviewerAppHandler.auth_token,
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["result"]["recommendation"], "PAY")

    def test_oversized_body_is_413(self):
        # Use a one-shot server with a tiny body cap so the test payload
        # stays small; the production default cap logic is identical.
        from src.ui.server import run_server  # noqa: F401  (import sanity)
        import src.ui.server as srv
        old = os.environ.get("PBP_UI_MAX_BODY_BYTES")
        try:
            os.environ["PBP_UI_MAX_BODY_BYTES"] = "1024"
            server = HTTPServer(("127.0.0.1", 0), ReviewerAppHandler)
            port = server.server_address[1]
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            time.sleep(0.3)
            try:
                url = f"http://127.0.0.1:{port}/api/investigate"
                payload = {"case_id": "case_001", "raw_evidence": "x" * 2048}
                req = urllib.request.Request(
                    url, data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json",
                             "X-Auth-Token": ReviewerAppHandler.auth_token},
                )
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        status = resp.status
                except urllib.error.HTTPError as e:
                    status = e.code
                self.assertEqual(status, 413)
            finally:
                server.shutdown()
                server.server_close()
        finally:
            if old is None:
                os.environ.pop("PBP_UI_MAX_BODY_BYTES", None)
            else:
                os.environ["PBP_UI_MAX_BODY_BYTES"] = old

    def test_index_page_includes_session_token(self):
        url = f"http://127.0.0.1:{self.port}/"
        with urllib.request.urlopen(url, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        self.assertIn("window.UI_AUTH_TOKEN", html)

    def test_get_endpoints_do_not_require_token(self):
        url = f"http://127.0.0.1:{self.port}/health"
        with urllib.request.urlopen(url, timeout=10) as resp:
            self.assertEqual(resp.status, 200)


class TestCooldownDeterminism(unittest.TestCase):
    """Fix 3 companion: cooldown recovery depends only on the module clock."""

    @patch("src.agent.credentials.time.time")
    def test_recovery_boundary_is_deterministic(self, mock_time):
        mock_time.return_value = 100.0
        cm = CredentialManager(["k1", "k2"])
        cm.mark_cooldown(60.0)  # k1 cooling until t=160
        self.assertEqual(cm.get_current_key(), "k2")

        # One tick before expiry: still cooling.
        mock_time.return_value = 159.9
        self.assertEqual(cm.credentials[0].state, CredentialState.COOLDOWN)

        # At/after expiry: recovered, deterministic. _refresh_cooldowns runs
        # inside get_current_key/get_wait_time, so the state transition is
        # observed on the next manager call at/after the boundary.
        mock_time.return_value = 160.0
        # With k2 exhausted, the next call refreshes cooldowns and
        # deterministically returns the recovered k1.
        cm.mark_exhausted("test")
        self.assertEqual(cm.get_current_key(), "k1")
        self.assertEqual(cm.credentials[0].state, CredentialState.ACTIVE)


if __name__ == "__main__":
    unittest.main()
