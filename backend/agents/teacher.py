from typing import Dict, Any
from backend.agents.base import BaseAgent
from backend.nlu.intents import Intent
from backend.tools.kit_client import kit_client
from backend.session_manager import create_pending_action

class TeacherAgent(BaseAgent):
    name = "teacher"

    def can_handle(self, intent: str, role: str) -> bool:
        teacher_intents = {
            Intent.GET_TEACHER_CLASSES.value,
            Intent.LIST_PENDING.value,
            Intent.APPROVE_REQUEST.value,
            Intent.REJECT_REQUEST.value
        }
        return intent in teacher_intents

    def handle(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        intent = ctx["intent"]
        role = ctx.get("role", "public")
        account_id = ctx.get("account_id")
        token = ctx.get("token")
        session_id = ctx["session_id"]
        
        if role != "teacher" or not account_id:
            return {
                "assistant_text": "Please log in with an authorized teacher account to access faculty workflows.",
                "module": self.name,
                "needs_confirmation": False
            }
            
        if intent == Intent.LIST_PENDING.value:
            pending = kit_client.list_pending_teacher_requests(account_id, token=token)
            if not pending:
                return {
                    "assistant_text": "There are currently no pending student requests awaiting review.",
                    "module": self.name
                }
            items_str = "; ".join(f"[{r['id']}] {r['student_name']}: {r['type']} on {r['date']} ({r['reason']})" for r in pending)
            return {
                "assistant_text": f"Here are the pending requests: {items_str}.",
                "module": self.name,
                "data": pending
            }
            
        elif intent == Intent.APPROVE_REQUEST.value:
            slots = ctx.get("slots", {})
            request_id = slots.get("request_id")
            
            if not request_id:
                ctx["awaiting_slot"] = "request_id"
                return {
                    "assistant_text": "Which request ID would you like to approve (e.g. 35 or REQ-9012)?",
                    "module": self.name,
                    "awaiting_slot": "request_id"
                }
                
            summary = f"Approve student request {request_id}"
            pending_action = create_pending_action(
                session_id=session_id,
                account_id=account_id,
                tool_name="approve_request",
                intent=intent,
                slots={"request_id": request_id, "action": "APPROVE"},
                summary=summary
            )
            return {
                "assistant_text": f"You are about to approve request {request_id}. Do you confirm this action?",
                "module": self.name,
                "pending_action": pending_action,
                "needs_confirmation": True
            }
            
        elif intent == Intent.REJECT_REQUEST.value:
            slots = ctx.get("slots", {})
            request_id = slots.get("request_id")
            
            if not request_id:
                ctx["awaiting_slot"] = "request_id"
                return {
                    "assistant_text": "Which request ID would you like to reject?",
                    "module": self.name,
                    "awaiting_slot": "request_id"
                }
                
            summary = f"Reject student request {request_id}"
            pending_action = create_pending_action(
                session_id=session_id,
                account_id=account_id,
                tool_name="reject_request",
                intent=intent,
                slots={"request_id": request_id, "action": "REJECT"},
                summary=summary
            )
            return {
                "assistant_text": f"You are about to reject request {request_id}. Do you confirm this action?",
                "module": self.name,
                "pending_action": pending_action,
                "needs_confirmation": True
            }

        return {"assistant_text": "Unsupported faculty operation.", "module": self.name}
