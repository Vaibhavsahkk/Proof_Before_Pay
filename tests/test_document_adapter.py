import io
import os
import json
import base64
import unittest
from unittest.mock import patch, MagicMock

import fitz  # PyMuPDF
from PIL import Image

from src.agent.document_adapter import DocumentAdapter, DocumentProcessingError
from src.agent.credentials import CredentialManager, CredentialState

class TestDocumentAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = DocumentAdapter()

    def _create_sample_pdf_bytes(self, text_content="Invoice Number: INV-999\nTotal: 500.00 USD\nVendor: ACME CORP"):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), text_content, fontsize=12)
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def _create_sample_image_bytes(self, width=100, height=100, color="white"):
        img = Image.new("RGB", (width, height), color=color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_process_valid_json(self):
        json_data = {"invoice": {"invoice_number": "INV-1001", "total": "605.00"}}
        raw_bytes = json.dumps(json_data).encode("utf-8")
        res = self.adapter.process_file("invoice.json", raw_bytes)
        self.assertIn("INV-1001", res)
        self.assertIn("605.00", res)

    def test_process_invalid_json_syntax(self):
        raw_bytes = b'{"invoice": {invalid json'
        with self.assertRaises(DocumentProcessingError) as ctx:
            self.adapter.process_file("bad.json", raw_bytes)
        self.assertIn("Invalid JSON syntax", str(ctx.exception))

    def test_process_valid_pdf_text_extraction(self):
        pdf_bytes = self._create_sample_pdf_bytes("Invoice: INV-2026\nVendor: Supplier A\nAmount: 1250.00 USD")
        res = self.adapter.process_file("sample_invoice.pdf", pdf_bytes)
        self.assertIn("=== DOCUMENT: sample_invoice.pdf (Format: PDF) ===", res)
        self.assertIn("INV-2026", res)
        self.assertIn("Supplier A", res)
        self.assertIn("1250.00 USD", res)

    def test_process_corrupted_pdf(self):
        corrupted_bytes = b"NOT_A_PDF_HEADER_DATA"
        with self.assertRaises(DocumentProcessingError) as ctx:
            self.adapter.process_file("corrupted.pdf", corrupted_bytes)
        self.assertIn("missing PDF magic header", str(ctx.exception))

    def test_process_valid_image(self):
        img_bytes = self._create_sample_image_bytes()
        # Mock Gemini multimodal OCR response
        mock_response = MagicMock()
        mock_response.text = "Invoice Number: INV-IMG-001\nTotal: 300.00 USD\nVendor: Image Supply Ltd"
        
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.models.generate_content.return_value = mock_response
            mock_client_cls.return_value = mock_client
            
            res = self.adapter.process_file("invoice.png", img_bytes, "image/png")
            self.assertIn("=== DOCUMENT: invoice.png", res)
            self.assertIn("INV-IMG-001", res)

    def test_process_corrupted_image(self):
        corrupted_img = b"\x89PNG\r\n\x1a\nCorruptedImageDataThatFailsPillowVerification"
        with self.assertRaises(DocumentProcessingError) as ctx:
            self.adapter.process_file("broken.png", corrupted_img, "image/png")
        self.assertIn("corrupted or unreadable image", str(ctx.exception))

    def test_process_unsupported_file_extension(self):
        with self.assertRaises(DocumentProcessingError) as ctx:
            self.adapter.process_file("malicious.exe", b"binary content")
        self.assertIn("Unsupported file format", str(ctx.exception))

    def test_process_empty_file(self):
        with self.assertRaises(DocumentProcessingError) as ctx:
            self.adapter.process_file("empty.pdf", b"")
        self.assertIn("is empty", str(ctx.exception))

    def test_process_multi_document_bundle(self):
        pdf_bytes = self._create_sample_pdf_bytes("Invoice: INV-MULTI-1\nTotal: 400.00 USD")
        po_bytes = self._create_sample_pdf_bytes("PO: PO-MULTI-1\nVendor: Global Parts")
        json_bytes = json.dumps({"vendor_master": {"vendor_name": "Global Parts", "tax_id": "TX-123"}}).encode("utf-8")

        files = [
            {"name": "inv.pdf", "data": pdf_bytes, "type": "application/pdf"},
            {"name": "po.pdf", "data": po_bytes, "type": "application/pdf"},
            {"name": "vm.json", "data": json_bytes, "type": "application/json"}
        ]

        bundle_str, metadata = self.adapter.process_bundle(files)
        self.assertEqual(len(metadata), 3)
        self.assertEqual(metadata[0]["name"], "inv.pdf")
        self.assertEqual(metadata[1]["name"], "po.pdf")
        self.assertEqual(metadata[2]["name"], "vm.json")
        self.assertIn("=== DOCUMENT: inv.pdf", bundle_str)
        self.assertIn("=== DOCUMENT: po.pdf", bundle_str)
        self.assertIn("vendor_name", bundle_str)

if __name__ == "__main__":
    unittest.main()
