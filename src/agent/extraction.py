import json
import os
import time
from typing import Dict, Any, Tuple
from google import genai
from google.genai import types

class ExtractionError(Exception):
    pass

class LLMExtractor:
    def __init__(self, api_key: str = None, model_id: str = "gemini-3.6-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for LLM extraction.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = model_id

    def extract_evidence(self, raw_bundle_str: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Uses the LLM to semantically map the raw evidence bundle into a structured format.
        """
        prompt = (
            "You are a strict data extraction assistant. Your job is to extract all evidence from the provided document bundle. "
            "Extract the exact strings and numbers. DO NOT perform any arithmetic. DO NOT apply business logic. "
            "Output the data as a well-formed JSON object containing the case_id, invoice, purchase_order, goods_receipt, "
            "vendor_master, prior_payment_history, and bank_change_evidence.\n\n"
            f"Evidence Bundle:\n{raw_bundle_str}"
        )
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json"
                    )
                )
                
                # Check if it returned a valid JSON
                data = json.loads(response.text)
                return data
            except Exception as e:
                if attempt == max_retries:
                    raise ExtractionError(f"Failed to extract evidence after {max_retries} retries: {str(e)}") from e
                time.sleep(1)

    def generate_explanation(self, findings: list) -> Tuple[str, str]:
        """
        Generates human-readable explanation and next steps based on the findings.
        Returns: (uncertainty_text, required_human_next_step_text)
        """
        if not findings:
            return "No material uncertainty identified.", "A human reviewer must make the final decision to approve the PAY recommendation."
            
        prompt = (
            "You are a financial investigator assistant. The deterministic rule engine has identified the following anomalies "
            f"in a payment request: {json.dumps(findings)}.\n\n"
            "Write a brief explanation of the uncertainty, and formulate a clear, actionable next step for a human reviewer. "
            "Output JSON with two keys: 'uncertainty' (string) and 'required_human_next_step' (string)."
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            return data.get("uncertainty", "Uncertainty exists due to identified anomalies."), data.get("required_human_next_step", "Human review required.")
        except Exception as e:
            return f"Failed to generate explanation: {str(e)}", "Manual investigation required by human reviewer."
