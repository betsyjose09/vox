"""
Central Policy & Security Agent for KIT Voice Assistant.
Enforces role-based access control (RBAC), tool allowlisting, state-changing confirmations,
calendar conflict checks, ownership validation, and prompt injection defense.
"""
from typing import Dict, Any, Tuple, Optional, Set
from datetime import date, datetime, timedelta
from backend.security.permissions import is_tool_allowed, ROLE_TOOL_ALLOWLIST
from backend.security.policy import check_exam_conflict, resolve_date_string

class PolicySecurityAgent:
    name = "policy_security"

    def __init__(self):
        self.allowed_tools = ROLE_TOOL_ALLOWLIST

    def check_authorization(self, role: str, tool_name: str) -> Tuple[bool, str]:
        """Validates whether the user's role has permission to execute the specified tool."""
        if not is_tool_allowed(role, tool_name):
            return False, f"Permission Denied: Role '{role}' is not authorized to execute '{tool_name}'."
        return True, "Authorized"

    def sanitize_untrusted_input(self, text: str) -> str:
        """Strips potential prompt injection markers and control delimiters."""
        if not text:
            return ""
        # Strip potential prompt jailbreak markers
        sanitized = text.replace("system:", "").replace("assistant:", "").replace("###", "")
        return sanitized.strip()

    def validate_leave_request(self, account_id: str, date_str: str, reason: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Enforces institutional leave policy (exam dates, minimum reason length)."""
        clean_date = resolve_date_string(date_str)
        if not clean_date:
            return False, "A valid leave date is required.", {}

        clean_reason = self.sanitize_untrusted_input(reason)
        if not clean_reason or len(clean_reason) < 3:
            return False, "A valid reason for leave is required (minimum 3 characters).", {}

        # Exam calendar conflict check (fails closed if calendar unavailable)
        has_conflict, conflict_msg = check_exam_conflict(clean_date)
        if has_conflict:
            return False, f"Leave policy conflict: {conflict_msg}", {}

        return True, "Policy check passed.", {"date": clean_date, "reason": clean_reason}

    def validate_od_request(self, account_id: str, date_str: str, event_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Enforces institutional On-Duty policy (event validation, exam conflicts)."""
        clean_date = resolve_date_string(date_str)
        if not clean_date:
            return False, "A valid On-Duty date is required.", {}

        clean_event = self.sanitize_untrusted_input(event_name)
        if not clean_event or len(clean_event) < 3:
            return False, "An event or symposium name is required for On-Duty.", {}

        has_conflict, conflict_msg = check_exam_conflict(clean_date)
        if has_conflict:
            return False, f"On-Duty policy conflict: {conflict_msg}", {}

        return True, "Policy check passed.", {"date": clean_date, "event_name": clean_event}

    def validate_confirmation(self, pending_action: Dict[str, Any], session_account_id: str) -> Tuple[bool, str]:
        """Validates that confirmation comes from the authentic owner of the pending action."""
        if not pending_action:
            return False, "No active pending action found for confirmation."
        if pending_action.get("account_id") != session_account_id:
            return False, "Action ownership mismatch: Confirmation must be made by the initiating account."
        return True, "Confirmation validated."

policy_agent = PolicySecurityAgent()

