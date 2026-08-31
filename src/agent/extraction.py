import json
import os
import re
import time
from typing import Dict, Any, Tuple, List
from google import genai
from google.genai import types

from src.agent.credentials import CredentialManager, RetrySignal

class ExtractionError(Exception):
    pass

class LLMExtractor:
    def __init__(self, api_key: str = None, model_id: str = "gemini-3.6-flash", credential_manager: CredentialManager = None):
        if credential_manager:
            self.cred_manager = credential_manager
        else:
            explicit_keys = [k.strip() for k in api_key.split(",")] if api_key else None
            self.cred_manager = CredentialManager(explicit_keys=explicit_keys)
        self.model_id = model_id

    def extract_evidence(self, case_id: str, raw_bundle_str: str, max_retries: int = 20) -> Dict[str, Any]:
        """
        Uses the LLM to semantically map the raw evidence bundle into a structured format.
        Rotates automatically across keys when rate limits / 429 are encountered.
        """
        cache_dir = "data/cache/extractions"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{case_id}.json")
        if case_id != "case_000" and os.path.exists(cache_file):
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
                # This may raise RetrySignal if all keys are in cooldown/exhausted
                current_key = self.cred_manager.get_current_key()
                client = genai.Client(api_key=current_key)
                response = client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )

                data = json.loads(response.text)
                if case_id != "case_000":
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                return data
            except RetrySignal:
                raise
            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
                    # Key is rate limited
                    if "quota" in err_str.lower():
                        self.cred_manager.mark_exhausted(reason="Quota Exceeded")
                    else:
                        self.cred_manager.mark_cooldown(cooldown_seconds=60.0)

                    # Raise RetrySignal so orchestrator handles the retry / cooldown wait
                    raise RetrySignal(f"Key rate limited: {err_str}")
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

        for attempt in range(max_retries + 1):
            try:
                current_key = self.cred_manager.get_current_key()
                client = genai.Client(api_key=current_key)
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
            except RetrySignal:
                raise
            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str or "quota" in err_str.lower():
                    if "quota" in err_str.lower():
                        self.cred_manager.mark_exhausted(reason="Quota Exceeded")
                    else:
                        self.cred_manager.mark_cooldown(cooldown_seconds=60.0)

                    raise RetrySignal(f"Key rate limited: {err_str}")
                else:
                    if attempt == max_retries:
                        return f"Failed to generate explanation: {err_str}", "Manual investigation required by human reviewer."
                    time.sleep(2)
