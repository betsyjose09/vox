from datetime import date, datetime, timedelta
from typing import Dict, Any, Tuple
from backend.tools.kit_client import kit_client

def resolve_date_string(date_str: str) -> str:
    """Resolves relative date words like 'today' or 'tomorrow' to YYYY-MM-DD."""
    clean = date_str.strip().lower()
    today = date.today()
    if clean == "today":
        return today.isoformat()
    elif clean == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    return clean

def check_exam_conflict(target_date: str) -> Tuple[bool, str]:
    """
    Checks if target date conflicts with any scheduled college examination.
    Fails closed if the calendar cannot be verified.
    """
    try:
        exams = kit_client.get_calendar_exams()
    except Exception as e:
        # FAIL CLOSED: cannot verify calendar
        return True, f"Security check failed: College academic calendar could not be verified ({str(e)})."
        
    for exam in exams:
        if exam["date"] == target_date:
            return True, f"Date {target_date} conflicts with scheduled examination: {exam['subject']} ({exam.get('time', 'TBD')})."
            
    return False, ""

def validate_leave_policy(account_id: str, date_str: str, reason: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Deterministic policy validation for student leave requests."""
    resolved_date = resolve_date_string(date_str)
    
    if not resolved_date:
        return False, "A valid leave date is required.", {}
        
    if not reason or len(reason.strip()) < 3:
        return False, "A valid reason for leave is required.", {}
        
    has_conflict, conflict_reason = check_exam_conflict(resolved_date)
    if has_conflict:
        return False, conflict_reason, {}
        
    return True, "Policy checks passed.", {"date": resolved_date, "reason": reason.strip()}

def validate_od_policy(account_id: str, date_str: str, event_name: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Deterministic policy validation for On-Duty requests."""
    resolved_date = resolve_date_string(date_str)
    
    if not resolved_date:
        return False, "A valid On-Duty date is required.", {}
        
    if not event_name or len(event_name.strip()) < 3:
        return False, "An event or symposium name is required for On-Duty.", {}
        
    has_conflict, conflict_reason = check_exam_conflict(resolved_date)
    if has_conflict:
        return False, conflict_reason, {}
        
    return True, "Policy checks passed.", {"date": resolved_date, "event_name": event_name.strip()}
