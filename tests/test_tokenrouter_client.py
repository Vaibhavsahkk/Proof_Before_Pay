import base64
import json
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent.tokenrouter_client import TokenRouterClient, TokenRouterError
from src.agent.credentials import CredentialManager
from src.agent.extraction import LLMExtractor


def test_chat_completion_posts_openai_compatible_json(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": '{"ok":true}'}}]}

    def post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setenv("TOKENROUTER_API_KEY", "test-token")
    with patch("src.agent.tokenrouter_client.httpx.post", side_effect=post):
        client = TokenRouterClient(model_id="z-ai/glm-5.3:free")
        result = client.complete("Return JSON", response_format=True)

    assert result == '{"ok":true}'
    assert captured["url"].endswith("/chat/completions")
    assert captured["headers"]["Authorization"] == "Bearer test-token"
    assert captured["json"]["model"] == "z-ai/glm-5.3:free"
    assert captured["json"]["response_format"] == {"type": "json_object"}


def test_complete_with_image_uses_data_url(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "text"}}]}

    captured = {}

    def post(url, headers, json, timeout):
        captured["json"] = json
        return Response()

    monkeypatch.setenv("TOKENROUTER_API_KEY", "test-token")
    with patch("src.agent.tokenrouter_client.httpx.post", side_effect=post):
        TokenRouterClient(model_id="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free").complete_with_image(
            "invoice.png", b"png-bytes", "image/png", "Transcribe"
        )

    image_part = captured["json"]["messages"][0]["content"][1]
    assert image_part["type"] == "image_url"
    assert base64.b64encode(b"png-bytes").decode() in image_part["image_url"]["url"]


def test_missing_token_fails_without_network(monkeypatch):
    monkeypatch.delenv("TOKENROUTER_API_KEY", raising=False)
    with pytest.raises(TokenRouterError, match="TOKENROUTER_API_KEY"):
        TokenRouterClient(model_id="z-ai/glm-5.3:free")


def test_invalid_response_is_rejected(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": []}

    monkeypatch.setenv("TOKENROUTER_API_KEY", "test-token")
    with patch("src.agent.tokenrouter_client.httpx.post", return_value=Response()):
        with pytest.raises(TokenRouterError, match="choices"):
            TokenRouterClient(model_id="z-ai/glm-5.3:free").complete("Return JSON")


def test_tokenrouter_mode_does_not_load_gemini_keys_from_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GEMINI_API_KEYS=gemini-secret-one,gemini-secret-two\n"
        "TOKENROUTER_API_KEY=router-secret-with-more-than-20-chars\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_PROVIDER", "tokenrouter")
    monkeypatch.setenv("TOKENROUTER_ENV_FILE", str(env_file))
    monkeypatch.delenv("TOKENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("TOKENROUTER_API_KEYS", raising=False)

    manager = CredentialManager()

    assert [credential.api_key for credential in manager.credentials] == [
        "router-secret-with-more-than-20-chars"
    ]


def test_text_pdf_bundle_uses_deterministic_parser_without_provider():
    raw = """=== DOCUMENT: invoice.pdf (Format: PDF) ===
Invoice Number: INV-2101
Vendor: SYNTHETIC WIDGETS LLC
Tax ID: TX-9101
Bank Account: ACC-1011
Currency: USD
Tax Rate Percent: 10.00
Item WIDGET-A | Standard Widget | Quantity 100 | Unit Price 5.50 USD | Line Total 550.00 USD
Subtotal: 550.00 USD
Tax Amount: 55.00 USD
Total Amount: 605.00 USD
=== DOCUMENT: purchase_order.pdf (Format: PDF) ===
PO Number: PO-3101
Currency: USD
Tax Rate Percent: 10.00
Item WIDGET-A | Quantity 100 | Unit Price 5.50 USD
=== DOCUMENT: goods_receipt.pdf (Format: PDF) ===
GRN Number: GRN-4101
Item WIDGET-A | Quantity Accepted 100
=== DOCUMENT: vendor_master.pdf (Format: PDF) ===
Vendor Name: SYNTHETIC WIDGETS LLC
Tax ID: TX-9101
Bank Account: ACC-1011
"""
    data = LLMExtractor._extract_text_pdf_bundle(raw)
    assert data is not None
    assert data["invoice"]["total"] == "605.00"
    assert data["purchase_order"]["items"][0]["unit_price"] == "5.50"