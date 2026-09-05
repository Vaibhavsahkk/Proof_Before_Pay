import os
import json
from src.agent.orchestrator import AgentOrchestrator
from src.agent.credentials import CredentialManager, CredentialState, RetrySignal
from src.agent.extraction import LLMExtractor
from unittest.mock import patch, MagicMock
import google.genai as _genai

def demo():
    print("==================================================")
    print("EXECUTOR â€” REQUIRED RECOVERY DEMONSTRATION")
    print("==================================================")

    # 1. Start CASE N â€” case_000 is cache-exempt in the extractor (the
    # cache write/read guard skips it), so this demo always exercises the
    # LIVE mocked API path instead of returning a stale cached extraction.
    case_id = "case_000"
    raw_evidence = '{"dummy": "data"}'

    # We will mock the CredentialManager and the API to force a 429 on credential A, then succeed on credential B
    os.environ["GEMINI_API_KEYS"] = "valid_key_A,valid_key_B,valid_key_C,valid_key_D,valid_key_E"

    orchestrator = AgentOrchestrator()

    # 5 credentials loaded
    print(f"Loaded credentials: {len(orchestrator.extractor.cred_manager.credentials)}")
    for i, c in enumerate(orchestrator.extractor.cred_manager.credentials):
        print(f"Slot {i}: {c.masked_key} - {c.state.value}")

    call_count = 0
    # The extractor creates a fresh genai.Client per attempt (see
    # extract_evidence), so there is no persistent `.client` to patch.
    # Patch the SDK's Client.models property so every client built by the
    # extractor returns the same mock models object.

    def _masked_current() -> str:
        cm = orchestrator.extractor.cred_manager
        for c in cm.credentials:
            if c.state.value == "ACTIVE" and c.key == cm.get_current_key():
                return c.masked_key
        return "<masked>"

    class _FakeModels:
        @staticmethod
        def generate_content(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            print(f"\n[API Call {call_count}] Attempting API request with key: {_masked_current()}")

            if call_count == 1:
                # 2. Force credential A to return retryable 429
                # 3. Record exact failure stage
                print("[FAILOVER TRIGGER] Forcing 429 RESOURCE_EXHAUSTED on first credential...")
                raise Exception("429 RESOURCE_EXHAUSTED")

            print("[SUCCESS] API request succeeded!")
            # 7. Complete CASE N
            mock_resp = MagicMock()
            contents = kwargs.get('contents', '')
            if isinstance(contents, str) and contents.startswith("You are a financial investigator"):
                mock_resp.text = json.dumps({"uncertainty": "test", "required_human_next_step": "test"})
            else:
                mock_resp.text = json.dumps({
                    "case_id": case_id,
                    "invoice": {"total": 100, "currency": "USD"},
                    "billing_history": []
                })
            return mock_resp

    with patch.object(_genai.Client, 'models', _FakeModels()):
        print("\nStarting workflow execution...")
        result = orchestrator.run_workflow(case_id, raw_evidence)

    print("\nWorkflow Complete.")
    print("Final Result:", json.dumps(result, indent=2))

    print("\nVerifying recovery:")
    for i, c in enumerate(orchestrator.extractor.cred_manager.credentials):
        print(f"Slot {i}: {c.masked_key} - {c.state.value}")

if __name__ == "__main__":
    demo()
