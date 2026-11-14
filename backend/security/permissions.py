from typing import Set, Dict

ROLE_TOOL_ALLOWLIST: Dict[str, Set[str]] = {
    "public": {
        "get_college_info",
        "get_courses",
        "get_eligibility",
        "search_knowledge",
        "get_holidays",
        "get_exam_dates"
    },
    "student": {
        "get_college_info",
        "get_courses",
        "get_eligibility",
        "search_knowledge",
        "get_holidays",
        "get_exam_dates",
        "get_attendance",
        "get_timetable",
        "get_my_requests",
        "submit_leave",
        "submit_on_duty"
    },
    "teacher": {
        "get_college_info",
        "get_courses",
        "get_eligibility",
        "search_knowledge",
        "get_holidays",
        "get_exam_dates",
        "get_teacher_classes",
        "list_pending_requests",
        "get_request_details",
        "approve_request",
        "reject_request"
    }
}

def is_tool_allowed(role: str, tool_name: str) -> bool:
    """Checks whether the authenticated role is authorized to execute the tool."""
    allowed_tools = ROLE_TOOL_ALLOWLIST.get(role, set())
    return tool_name in allowed_tools

