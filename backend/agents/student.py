from typing import Dict, Any
from backend.agents.base import BaseAgent
from backend.nlu.intents import Intent
from backend.tools.kit_client import kit_client
from backend.security.policy import validate_leave_policy, validate_od_policy
from backend.session_manager import create_pending_action

class StudentAgent(BaseAgent):
    name = "student"

    def can_handle(self, intent: str, role: str) -> bool:
        student_intents = {
            Intent.GET_ATTENDANCE.value,
            Intent.GET_TIMETABLE.value,
            Intent.GET_MY_REQUESTS.value,
            Intent.SUBMIT_LEAVE.value,
            Intent.SUBMIT_ON_DUTY.value
        }
        return intent in student_intents

    def handle(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        intent = ctx["intent"]
        role = ctx.get("role", "public")
        account_id = ctx.get("account_id")
        token = ctx.get("token")
        session_id = ctx["session_id"]
        
        # Security check: student personal tools require student role and verified account
        if role != "student" or not account_id:
            return {
                "assistant_text": "Please log in with your student account first to access your personal student records.",
                "module": self.name,
                "needs_confirmation": False
            }
            
        if intent == Intent.GET_ATTENDANCE.value:
            res = kit_client.get_attendance(account_id, token=token)
            if not res.get("success"):
                return {"assistant_text": "Unable to retrieve attendance record at this time.", "module": self.name}
                
            overall = res["overall_pct"]
            name = res.get("name", "Student")
            breakdown_str = ", ".join(f"{b['subject']}: {b['pct']}%" for b in res.get("breakdown", []))
            
            return {
                "assistant_text": f"Your overall attendance is {overall}% ({name}). Subject breakdown: {breakdown_str}.",
                "module": self.name,
                "data": res
            }
            
        elif intent == Intent.GET_TIMETABLE.value:
            res = kit_client.get_timetable(account_id, token=token)
            if not res.get("success"):
                return {"assistant_text": "Unable to retrieve timetable at this time.", "module": self.name}
            schedule_str = "; ".join(f"{item['day']}: {item['schedule']}" for item in res.get("timetable", []))
            return {
                "assistant_text": f"Here is your timetable schedule: {schedule_str}.",
                "module": self.name,
                "data": res
            }
            
        elif intent == Intent.GET_MY_REQUESTS.value:
            requests = kit_client.get_student_requests(account_id, token=token)
            if not requests:
                return {"assistant_text": "You have no active or past requests recorded.", "module": self.name}
            req_str = "; ".join(f"[{r['id']}] {r['type']} on {r['date']} ({r['status']})" for r in requests)
            return {
                "assistant_text": f"Here are your requests: {req_str}.",
                "module": self.name,
                "data": requests
            }
            
        elif intent == Intent.SUBMIT_LEAVE.value:
            slots = ctx.get("slots", {})
            leave_date = slots.get("date")
            reason = slots.get("reason")
            
            # Step 1: Collect missing date
            if not leave_date:
                ctx["awaiting_slot"] = "date"
                return {
                    "assistant_text": "Which date do you need leave for (e.g. today, tomorrow, or YYYY-MM-DD)?",
                    "module": self.name,
                    "updated_slots": slots,
                    "awaiting_slot": "date"
                }
                
            # Step 2: Collect missing reason
            if not reason:
                ctx["awaiting_slot"] = "reason"
                return {
                    "assistant_text": f"What is the reason for your leave on {leave_date}?",
                    "module": self.name,
                    "updated_slots": slots,
                    "awaiting_slot": "reason"
                }
                
            # Step 3: Run deterministic policy checks (e.g. Exam conflict check)
            policy_ok, policy_msg, validated_slots = validate_leave_policy(account_id, leave_date, reason)
            if not policy_ok:
                return {
                    "assistant_text": f"Leave request blocked: {policy_msg}",
                    "module": self.name,
                    "rejected_by_policy": True
                }
                
            # Step 4: Create pending action requiring explicit confirmation
            summary = f"Leave request for {validated_slots['date']} due to '{validated_slots['reason']}'"
            pending_action = create_pending_action(
                session_id=session_id,
                account_id=account_id,
                tool_name="submit_leave",
                intent=intent,
                slots=validated_slots,
                summary=summary
            )
            
            return {
                "assistant_text": f"You are requesting leave for {validated_slots['date']} because of {validated_slots['reason']}. Shall I submit this request?",
                "module": self.name,
                "pending_action": pending_action,
                "needs_confirmation": True
            }
            
        elif intent == Intent.SUBMIT_ON_DUTY.value:
            slots = ctx.get("slots", {})
            od_date = slots.get("date")
            event_name = slots.get("event_name")
            
            if not od_date:
                ctx["awaiting_slot"] = "date"
                return {
                    "assistant_text": "Which date do you need On-Duty (OD) for?",
                    "module": self.name,
                    "updated_slots": slots,
                    "awaiting_slot": "date"
                }
            if not event_name:
                ctx["awaiting_slot"] = "event_name"
                return {
                    "assistant_text": f"What is the event or symposium name for your On-Duty on {od_date}?",
                    "module": self.name,
                    "updated_slots": slots,
                    "awaiting_slot": "event_name"
                }
                
            policy_ok, policy_msg, validated_slots = validate_od_policy(account_id, od_date, event_name)
            if not policy_ok:
                return {
                    "assistant_text": f"On-Duty request blocked: {policy_msg}",
                    "module": self.name,
                    "rejected_by_policy": True
                }
                
            summary = f"On-Duty request for {validated_slots['date']} for event '{validated_slots['event_name']}'"
            pending_action = create_pending_action(
                session_id=session_id,
                account_id=account_id,
                tool_name="submit_on_duty",
                intent=intent,
                slots=validated_slots,
                summary=summary
            )
            
            return {
                "assistant_text": f"You are requesting On-Duty for {validated_slots['date']} for '{validated_slots['event_name']}'. Shall I submit this request?",
                "module": self.name,
                "pending_action": pending_action,
                "needs_confirmation": True
            }

        return {"assistant_text": "Unsupported student operation.", "module": self.name}
