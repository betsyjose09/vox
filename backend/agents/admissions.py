from typing import Dict, Any
from backend.agents.base import BaseAgent
from backend.nlu.intents import Intent
from backend.tools.kit_client import kit_client

class AdmissionsAgent(BaseAgent):
    name = "admissions"

    def can_handle(self, intent: str, role: str) -> bool:
        admissions_intents = {
            Intent.GET_COLLEGE_INFO.value,
            Intent.GET_COURSES.value,
            Intent.GET_ELIGIBILITY.value,
            Intent.GET_FEES.value,
            Intent.GET_HOLIDAYS.value,
            Intent.GET_EXAM_DATES.value
        }
        return intent in admissions_intents

    def handle(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        intent = ctx["intent"]
        
        if intent == Intent.GET_COLLEGE_INFO.value:
            info = kit_client.get_college_info()
            return {
                "assistant_text": f"{info['name']} ({info['accreditation']}). Motto: '{info['motto']}'. Located at {info['location']}. Contact: {info['helpline']} | {info['email']}.",
                "module": self.name,
                "data": info
            }
            
        elif intent in [Intent.GET_COURSES.value, Intent.GET_FEES.value]:
            courses = kit_client.get_courses()
            course_list = "; ".join(f"{c['title']} (Fee: {c['annual_fee']}/year, {c['seats']} seats)" for c in courses)
            return {
                "assistant_text": f"KIT offers the following programs: {course_list}.",
                "module": self.name,
                "data": courses
            }
            
        elif intent == Intent.GET_ELIGIBILITY.value:
            courses = kit_client.get_courses()
            elig_str = "; ".join(f"{c['code']}: {c['eligibility']}" for c in courses)
            return {
                "assistant_text": f"KIT Admission Requirements: {elig_str}.",
                "module": self.name,
                "data": courses
            }
            
        elif intent == Intent.GET_HOLIDAYS.value:
            holidays = kit_client.get_calendar_holidays()
            h_str = ", ".join(f"{h['name']} ({h['date']})" for h in holidays)
            return {
                "assistant_text": f"Upcoming college holidays: {h_str}.",
                "module": self.name,
                "data": holidays
            }
            
        elif intent == Intent.GET_EXAM_DATES.value:
            exams = kit_client.get_calendar_exams()
            e_str = "; ".join(f"{e['subject']} on {e['date']} ({e['time']})" for e in exams)
            return {
                "assistant_text": f"Official examination schedule: {e_str}.",
                "module": self.name,
                "data": exams
            }

        return {"assistant_text": "Unsupported admissions query.", "module": self.name}
