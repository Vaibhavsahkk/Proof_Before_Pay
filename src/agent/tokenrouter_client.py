import base64
import os
from typing import Any, Dict, Optional

import httpx


class TokenRouterError(Exception):
    """Raised when the OpenAI-compatible TokenRouter contract fails."""


class TokenRouterClient:
    def __init__(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.api_key = api_key or os.environ.get("TOKENROUTER_API_KEY", "").strip()
        if not self.api_key:
            raise TokenRouterError("TOKENROUTER_API_KEY is not configured")
        self.model_id = model_id
        self.base_url = (base_url or os.environ.get(
            "TOKENROUTER_BASE_URL", "https://api.tokenrouter.com/v1"
        )).rstrip("/")
        self.timeout = timeout

    def complete(self, prompt: str, response_format: bool = False) -> str:
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        if response_format:
            payload["response_format"] = {"type": "json_object"}
        return self._post(payload)

    def complete_with_image(
        self, filename: str, content_bytes: bytes, mime_type: str, prompt: str
    ) -> str:
        encoded = base64.b64encode(content_bytes).decode("ascii")
        payload = {
            "model": self.model_id,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{prompt}\nFilename: {filename}"},
                    {"type": "image_url", "image_url": {
                        "url": f"data:{mime_type};base64,{encoded}"
                    }},
                ],
            }],
            "temperature": 0,
        }
        return self._post(payload)

    def _post(self, payload: Dict[str, Any]) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
            choices = body.get("choices")
            if not choices:
                raise TokenRouterError("TokenRouter response has no choices")
            content = choices[0].get("message", {}).get("content")
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            if not isinstance(content, str) or not content.strip():
                raise TokenRouterError("TokenRouter response has no message content")
            return content.strip()
        except TokenRouterError:
            raise
        except httpx.HTTPStatusError as exc:
            raise TokenRouterError(
                f"TokenRouter HTTP {exc.response.status_code}: {exc.response.text[:500]}"
            ) from exc
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            raise TokenRouterError(f"TokenRouter request failed: {exc}") from exc