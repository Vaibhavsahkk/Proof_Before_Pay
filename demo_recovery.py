import os
import json
from src.agent.orchestrator import AgentOrchestrator
from src.agent.credentials import CredentialManager, CredentialState, RetrySignal
from unittest.mock import patch, MagicMock

def demo():
    print("==================================================")
    print("EXECUTOR — REQUIRED RECOVERY DEMONSTRATION")
    print("==================================================")

    # 1. Start CASE N
    case_id = "case_010"
    raw_evidence = '{"dummy": "data"}'
    
    # We will mock the CredentialManager and the API to force a 429 on credential A, then succeed on credential B
    os.environ["GEMINI_API_KEYS"] = "valid_key_A,valid_key_B,valid_key_C,valid_key_D,valid_key_E"
    
    orchestrator = AgentOrchestrator()
    
    # 5 credentials loaded
    print(f"Loaded credentials: {len(orchestrator.extractor.cred_manager.credentials)}")
    for i, c in enumerate(orchestrator.extractor.cred_manager.credentials):
        print(f"Slot {i}: {c.masked_key} - {c.state.value}")
        
    call_count = 0
    original_generate = orchestrator.extractor.client.models.generate_content
    
    def fake_generate_content(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        print(f"\n[API Call {call_count}] Attempting API request with key: {orchestrator.extractor.cred_manager.get_current_key()}")
        
        if call_count == 1:
            # 2. Force credential A to return retryable 429
            # 3. Record exact failure stage
            print("[FAILOVER TRIGGER] Forcing 429 RESOURCE_EXHAUSTED on first credential...")
            raise Exception("429 RESOURCE_EXHAUSTED")
            
        print("[SUCCESS] API request succeeded!")
        # 7. Complete CASE N
        mock_resp = MagicMock()
        if kwargs.get('contents', '').startswith("You are a financial investigator"):
            mock_resp.text = json.dumps({"uncertainty": "test", "required_human_next_step": "test"})
        else:
            mock_resp.text = json.dumps({
                "case_id": case_id,
                "invoice": {"total": 100, "currency": "USD"},
                "billing_history": []
            })
        return mock_resp

    with patch.object(orchestrator.extractor.client.models, 'generate_content', side_effect=fake_generate_content):
        print("\nStarting workflow execution...")
        result = orchestrator.run_workflow(case_id, raw_evidence)
        
    print("\nWorkflow Complete.")
    print("Final Result:", json.dumps(result, indent=2))
    
    print("\nVerifying recovery:")
    for i, c in enumerate(orchestrator.extractor.cred_manager.credentials):
        print(f"Slot {i}: {c.masked_key} - {c.state.value}")
        
if __name__ == "__main__":
    demo()
