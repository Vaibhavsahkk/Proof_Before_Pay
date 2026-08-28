import sys

def request_human_approval(action: str, reason: str, risk: str, expected_result: str, consequence_if_declined: str) -> bool:
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
    
    while True:
        choice = input("Do you approve this action? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            print("[✓] Action approved by human.")
            return True
        elif choice in ['n', 'no']:
            print("[✗] Action declined by human.")
            return False
        else:
            print("Please enter 'y' or 'n'.")
