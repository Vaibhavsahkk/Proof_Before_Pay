import sys
import getpass
from typing import Any, Optional
from src.utils.logger import TraceLogger, TraceLoggerError

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
    Audits the decision BEFORE allowing execution. Fails closed if audit logging fails.
    Returns True if approved and audited successfully, False otherwise.
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
    
    proposed_approval = False
    try:
        if not sys.stdin.isatty():
            print("[DECLINED] Non-interactive execution detected. Action declined by default for safety.")
            proposed_approval = False
        else:
            while True:
                choice = input("Do you approve this action? (y/n): ").strip().lower()
                if choice in ['y', 'yes']:
                    proposed_approval = True
                    break
                elif choice in ['n', 'no']:
                    proposed_approval = False
                    break
                else:
                    print("Please enter 'y' or 'n'.")
    except (EOFError, KeyboardInterrupt):
        print("\n[DECLINED] Input interrupted or EOF reached. Action declined for safety.")
        proposed_approval = False

    # Instantiate default TraceLogger if none provided
    active_logger = logger if logger is not None else TraceLogger()

    # Determine user identity safely
    try:
        approved_by = getpass.getuser()
    except Exception:
        approved_by = "unknown"

    # MANDATORY AUDIT LOGGING BEFORE PROCEEDING
    try:
        active_logger.log_event(
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
                "decision": "APPROVED" if proposed_approval else "DECLINED",
                "approved_by": approved_by
            },
            result="SUCCESS" if proposed_approval else "DECLINED"
        )
    except Exception as e:
        # FAIL CLOSED: If audit logging fails, force decision to False even if human said Yes!
        print(f"[ERROR] Audit logging failed: {e}. FAILING CLOSED for security.")
        return False

    if proposed_approval:
        print("[SUCCESS] Action approved by human and audit log written.")
        return True
    else:
        print("[DECLINED] Action declined.")
        return False
