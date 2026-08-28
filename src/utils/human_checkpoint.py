import sys
import getpass
import re
from typing import Any, Optional
from src.utils.logger import TraceLogger, TraceLoggerError

def _validate_ui_safety(val: str, max_len: int = 100) -> str:
    """Rejects fields that exceed length or contain unsafe formatting characters."""
    val = str(val)
    if len(val) > max_len:
        raise ValueError("Field exceeds maximum safe length.")
    
    # ANSI escape sequences (CSI and OSC)
    if re.search(r'\x1b\[[0-9;]*[a-zA-Z]', val) or re.search(r'\x1b\]', val):
        raise ValueError("Field contains ANSI escape sequences.")
        
    # Control characters (\x00-\x1f, \x7f-\x9f) including newlines, carriage returns
    if re.search(r'[\x00-\x1f\x7f-\x9f]', val):
        raise ValueError("Field contains control characters or newlines.")
        
    # Unicode bidi and zero-width formatting characters
    # \u200B-\u200F (zero width spaces, LRM, RLM), \u202A-\u202E (bidi), \u2060-\u2069 (bidi, word joiners), \uFEFF
    if re.search(r'[\u200B-\u200F\u202A-\u202E\u2060-\u2069\uFEFF]', val):
        raise ValueError("Field contains unsafe Unicode formatting characters.")
        
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
    Audits the decision BEFORE allowing execution. Fails closed if audit logging fails
    or if UI fields contain unsafe characters.
    """
    active_logger = logger if logger is not None else TraceLogger()
    
    try:
        approved_by = getpass.getuser()
    except Exception:
        approved_by = "unknown"

    try:
        safe_action = _validate_ui_safety(action)
        safe_reason = _validate_ui_safety(reason)
        safe_risk = _validate_ui_safety(risk)
        safe_expected = _validate_ui_safety(expected_result)
        safe_consequence = _validate_ui_safety(consequence_if_declined)
    except ValueError as e:
        print(f"[DECLINED] UI Safety Validation Failed: {e}")
        try:
            active_logger.log_event(
                phase=phase, agent="human_checkpoint", action="request_approval", tool="human_input",
                input_data={"action_requested": action, "error": str(e)},
                output_data={"decision": "DECLINED", "approved_by": approved_by},
                result="DECLINED"
            )
        except Exception as audit_error:
            print(
                "[ERROR] Audit logging failed while recording rejected unsafe input: "
                f"{audit_error}. Action remains declined."
            )
        return False

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

    # MANDATORY AUDIT LOGGING BEFORE PROCEEDING
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
