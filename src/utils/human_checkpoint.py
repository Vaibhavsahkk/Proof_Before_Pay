import sys
import getpass
from typing import Any, Optional

def request_human_approval(
    action: str, 
    reason: str, 
    risk: str, 
    expected_result: str, 
    consequence_if_declined: str,
    logger: Optional[Any] = None,
    phase: str = "N/A"
) -> bool:
    """
    Pause execution and request explicit human approval for consequential actions.
    Returns True if approved, False if declined.
    """
    print("\n" + "="*60)
    print("HUMAN APPROVAL REQUIRED")
    print("="*60)
    print(f"Action: {action}")
    print(f"Reason: {reason}")
    print(f"Risk: {risk}")
    print(f"What will happen: {expected_result}")
    print(f"What happens if declined: {consequence_if_declined}")
    print("="*60)
    
    approved = False
    try:
        if not sys.stdin.isatty():
            # In non-interactive mode, fail safely
            print("[DECLINED] Non-interactive execution detected. Action declined by default for safety.")
            approved = False
        else:
            while True:
                choice = input("Do you approve this action? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    print("[SUCCESS] Action approved by human.")
                    approved = True
                    break
                elif choice in ['n', 'no']:
                    print("[DECLINED] Action declined by human.")
                    approved = False
                    break
                else:
                    print("Please enter 'y' or 'n'.")
    except (EOFError, KeyboardInterrupt):
        print("\n[DECLINED] Input interrupted or EOF reached. Action declined for safety.")
        approved = False

    # Auditable record
    if logger:
        try:
            approved_by = getpass.getuser()
        except:
            approved_by = "unknown"
            
        logger.log_event(
            phase=phase,
            agent="human_checkpoint",
            action="request_approval",
            tool="human_input",
            input_data={
                "action_requested": action,
                "action_description": expected_result,
                "reason": reason,
                "risk": risk
            },
            output_data={
                "decision": "APPROVED" if approved else "DECLINED",
                "approved_by": approved_by
            },
            result="SUCCESS"
        )
        
    return approved
