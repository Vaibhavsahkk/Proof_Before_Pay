import sys
import getpass
import re
from typing import Any, Optional
from src.utils.logger import TraceLogger, TraceLoggerError

def _sanitize_for_display(val: str, max_len: int = 100) -> str:
    """Escapes control characters, ANSI codes, and Bidi controls for safe terminal display."""
    val = str(val)
    # Remove ANSI escape sequences FIRST before \x1b is stripped
    val = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', val)
    # Remove control characters (including \n, \r, etc)
    val = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', val)
    # Remove Unicode Bidi controls
    val = re.sub(r'[\u202A-\u202E\u2066-\u2069]', '', val)
    if len(val) > max_len:
        return val[:max_len] + "..."
    return val

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
    safe_action = _sanitize_for_display(action)
    safe_reason = _sanitize_for_display(reason)
    safe_risk = _sanitize_for_display(risk)
    safe_expected = _sanitize_for_display(expected_result)
    safe_consequence = _sanitize_for_display(consequence_if_declined)

    print("\n" + "="*60)
    print("HUMAN APPROVAL REQUIRED")
    print("="*60)
    print(f"Action: {safe_action}")
    print(f"Reason: {safe_reason}")
    print(f"Risk: {safe_risk}")
    print(f"What will happen: {safe_expected}")
    print(f"What happens if declined: {safe_consequence}")
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

    try:
        approved_by = getpass.getuser()
    except Exception:
        approved_by = "unknown"

    try:
        active_logger.log_event(
            phase=phase,
            agent="human_checkpoint",
            action="request_approval",
            tool="human_input",
            input_data={
                "action_requested": safe_action,
                "action_description": safe_expected,
                "reason": safe_reason,
                "risk": safe_risk
            },
            output_data={
                "decision": "APPROVED" if proposed_approval else "DECLINED",
                "approved_by": approved_by
            },
            result="SUCCESS" if proposed_approval else "DECLINED"
        )
    except Exception as e:
        print(f"[ERROR] Audit logging failed: {e}. FAILING CLOSED for security.")
        return False

    if proposed_approval:
        print("[SUCCESS] Action approved by human and audit log written.")
        return True
    else:
        print("[DECLINED] Action declined.")
        return False
