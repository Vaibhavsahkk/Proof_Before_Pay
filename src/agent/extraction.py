import json
import os
import re
import time
from typing import Dict, Any, Tuple, List
from google import genai
from google.genai import types

class ExtractionError(Exception):
    pass

class APIKeyRotator:
    def __init__(self, explicit_keys: List[str] = None):
        self.keys = self._load_keys(explicit_keys)
        if not self.keys:
            raise ValueError("No Gemini API keys found. Please set GEMINI_API_KEYS or GEMINI_API_KEY in .env or environment.")
        self.current_index = 0
        self._client = None

    def _load_keys(self, explicit_keys: List[str] = None) -> List[str]:
        keys = []
        if explicit_keys:
            for k in explicit_keys:
                if k and k.strip():
                    keys.append(k.strip())
            if keys:
                return list(dict.fromkeys(keys))

        # Check environment variables
        env_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY")
        if env_keys:
            for part in re.split(r"[,;\n\s]+", env_keys.strip()):
                if part.startswith("AQ.") or part.startswith("AIza") or len(part) > 20:
                    keys.append(part.strip())

        # Check .env file directly if available
        if os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            val = line.split("=", 1)[1].strip()
                            for part in re.split(r"[,;\s]+", val):
                                if len(part) > 20:
                                    keys.append(part.strip())
                        elif len(line) > 20:
                            keys.append(line.strip())
            except Exception:
                pass

        # Deduplicate preserving order
        return list(dict.fromkeys(keys))

    @property
    def current_key(self) -> str:
        return self.keys[self.current_index]

    def get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.current_key)
        return self._client

    def rotate_to_next(self, reason: str = "") -> None:
        prev_idx = self.current_index
        self.current_index = (self.current_index + 1) % len(self.keys)
        self._client = genai.Client(api_key=self.current_key)
        print(f"[API KEY ROTATION] Key {prev_idx + 1}/{len(self.keys)} hit limit ({reason}). Rotated to Key {self.current_index + 1}/{len(self.keys)}.")

class LLMExtractor:
    def __init__(self, api_key: str = None, model_id: str = "gemini-3.6-flash"):
        explicit_keys = [api_key] if api_key else None
        self.rotator = APIKeyRotator(explicit_keys=explicit_keys)
        self.model_id = model_id

    def extract_evidence(self, case_id: str, raw_bundle_str: str, max_retries: int = 20) -> Dict[str, Any]:
        """
        Uses the LLM to semantically map the raw evidence bundle into a structured format.
        Rotates automatically across keys when rate limits / 429 are encountered.
        """
        cache_dir = "data/cache/extractions"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{case_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        prompt = (
            "You are a strict data extraction assistant. Your job is to extract all evidence from the provided document bundle. "
            "Extract the exact strings and numbers. DO NOT perform any arithmetic. DO NOT apply business logic. "
            "Output the data as a well-formed JSON object containing the case_id, invoice, purchase_order, goods_receipt, "
            "vendor_master, prior_payment_history, and bank_change_evidence.\n\n"
            f"Evidence Bundle:\n{raw_bundle_str}"
        )

        total_rotations = 0

        for attempt in range(max_retries + 1):
            try:
                client = self.rotator.get_client()
                response = client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )

                # Check if it returned a valid JSON
                data = json.loads(response.text)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return data
            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
                    self.rotator.rotate_to_next(reason="429 / Quota Limit")
                    total_rotations += 1
                    # If we have cycled through all keys, wait briefly before retrying
                    if total_rotations % len(self.rotator.keys) == 0:
                        print(f"All {len(self.rotator.keys)} keys rotated once. Waiting 15s before next cycle...")
                        time.sleep(15)
                    else:
                        time.sleep(1)
                else:
                    if attempt == max_retries:
                        raise ExtractionError(f"Failed to extract evidence after {max_retries} retries: {err_str}") from e
                    time.sleep(2)

    def generate_explanation(self, case_id: str, findings: list, max_retries: int = 20) -> Tuple[str, str]:
        """
        Generates human-readable explanation and next steps based on the findings.
        Returns: (uncertainty_text, required_human_next_step_text)
        """
        if not findings:
            return "No material uncertainty identified.", "A human reviewer must make the final decision to approve the PAY recommendation."

        cache_dir = "data/cache/explanations"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{case_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("uncertainty", ""), data.get("required_human_next_step", "")

        prompt = (
            "You are a financial investigator assistant. The deterministic rule engine has identified the following anomalies "
            f"in a payment request: {json.dumps(findings)}.\n\n"
            "Write a brief explanation of the uncertainty, and formulate a clear, actionable next step for a human reviewer. "
            "Output JSON with two keys: 'uncertainty' (string) and 'required_human_next_step' (string)."
        )

        total_rotations = 0
        for attempt in range(max_retries + 1):
            try:
                client = self.rotator.get_client()
                response = client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )
                data = json.loads(response.text)
                uncertainty = data.get("uncertainty", "Uncertainty exists due to identified anomalies.")
                next_step = data.get("required_human_next_step", "Human review required.")

                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump({"uncertainty": uncertainty, "required_human_next_step": next_step}, f, indent=2)

                return uncertainty, next_step
            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
                    self.rotator.rotate_to_next(reason="429 / Quota Limit")
                    total_rotations += 1
                    if total_rotations % len(self.rotator.keys) == 0:
                        print(f"All {len(self.rotator.keys)} keys rotated once. Waiting 15s before next cycle...")
                        time.sleep(15)
                    else:
                        time.sleep(1)
                else:
                    if attempt == max_retries:
                        return f"Failed to generate explanation: {err_str}", "Manual investigation required by human reviewer."
                    time.sleep(2)
