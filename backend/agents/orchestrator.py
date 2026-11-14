from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from backend.schemas import SessionData
from backend.session_manager import (
    get_session, create_session, get_conversation_state, save_conversation_state,
    get_active_pending_action_for_session, try_claim_action_for_execution,
    update_action_status, log_turn, get_history
)
from backend.llm.conversation_engine import conversation_engine
from backend.security.policy_agent import policy_agent
from backend.agents.response_agent import response_agent
from backend.agents.student import StudentAgent
from backend.agents.teacher import TeacherAgent
from backend.agents.admissions import AdmissionsAgent
from backend.agents.knowledge import KnowledgeAgent
from backend.tools.kit_client import kit_client

class MasterOrchestrator:
    def __init__(self):
        self.student_agent = StudentAgent()
        self.teacher_agent = TeacherAgent()
        self.admissions_agent = AdmissionsAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.response_agent = response_agent
        self.policy_agent = policy_agent
        self.agents = [
            self.student_agent,
            self.teacher_agent,
            self.admissions_agent,
            self.knowledge_agent
        ]

    def execute_pending_tool(self, pending_action: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Executes the specific allowlisted tool associated with a confirmed action."""
        tool_name = pending_action["tool_name"]
        account_id = pending_action["account_id"]
        slots = pending_action["slots"]
        idempotency_key = pending_action["idempotency_key"]
        
        if tool_name == "submit_leave":
            return kit_client.submit_leave_request(
                account_id=account_id,
                leave_date=slots["date"],
                reason=slots["reason"],
                idempotency_key=idempotency_key,
                token=token
            )
        elif tool_name == "submit_on_duty":
            return kit_client.submit_od_request(
                account_id=account_id,
                od_date=slots["date"],
                event_name=slots["event_name"],
                idempotency_key=idempotency_key,
                token=token
            )
        elif tool_name in ["approve_request", "reject_request"]:
            return kit_client.review_request(
                account_id=account_id,
                request_id=slots["request_id"],
                action=slots["action"],
                token=token,
                reason=slots.get("reason"),
                idempotency_key=idempotency_key
            )
        else:
            return {"success": False, "error": f"unrecognized_tool_{tool_name}"}

    def handle_turn(
        self,
        session_id: str,
        user_text: str,
        recognized_audio_text: Optional[str] = None
    ) -> Dict[str, Any]:
        session = get_session(session_id)
        if not session:
            session = create_session()
            session_id = session.session_id
            
        role = session.role
        account_id = session.account_id
        token = session.kit_token
        
        # 1. Determine effective input text
        effective_text = (user_text or recognized_audio_text or "").strip()
        if not effective_text:
            return {
                "session_id": session_id,
                "assistant_text": "I didn't catch that. Please speak a command or type your message.",
                "needs_confirmation": False
            }

        # 2. Retrieve state & history
        conv_state = get_conversation_state(session_id)
        history = get_history(session_id, account_id)
        active_pending = get_active_pending_action_for_session(session_id)

        # 3. LLM Conversational Understanding with deterministic fallback
        nlu = conversation_engine.interpret_user_turn(
            user_text=effective_text,
            conversation_history=history,
            active_context=conv_state
        )
        intent = nlu.intent
        entities = nlu.entities

        # 4. Handle Confirmation of an active pending action
        if active_pending:
            if intent == "CONFIRM_ACTION":
                # Validate confirmation security
                val_ok, val_err = self.policy_agent.validate_confirmation(active_pending, account_id)
                if not val_ok:
                    return {
                        "session_id": session_id,
                        "assistant_text": f"Confirmation blocked: {val_err}",
                        "needs_confirmation": False
                    }

                claimed = try_claim_action_for_execution(active_pending["id"], session_id)
                if not claimed:
                    reply = "Action could not be executed: it may have expired or already been completed."
                    return {
                        "session_id": session_id,
                        "recognized_text": recognized_audio_text,
                        "intent": "CONFIRM_ACTION",
                        "module": "orchestrator",
                        "assistant_text": reply,
                        "needs_confirmation": False
                    }
                    
                result = self.execute_pending_tool(claimed, token=token)
                if result.get("success"):
                    update_action_status(claimed["id"], "SUCCEEDED", result)
                    reply = f"Confirmed. Your action was executed successfully. {result.get('message', '')}"
                else:
                    update_action_status(claimed["id"], "FAILED", result)
                    reply = f"The action could not be completed. Error: {result.get('error', 'Execution failure')}"
                    
                save_conversation_state(session_id, {})
                log_turn(session_id, account_id, effective_text, reply, "CONFIRM_ACTION", "orchestrator")
                return {
                    "session_id": session_id,
                    "recognized_text": recognized_audio_text,
                    "intent": "CONFIRM_ACTION",
                    "module": "orchestrator",
                    "assistant_text": reply,
                    "needs_confirmation": False
                }
                
            elif intent == "CANCEL_ACTION":
                update_action_status(active_pending["id"], "CANCELLED")
                save_conversation_state(session_id, {})
                reply = "The pending action was cancelled."
                log_turn(session_id, account_id, effective_text, reply, "CANCEL_ACTION", "orchestrator")
                return {
                    "session_id": session_id,
                    "recognized_text": recognized_audio_text,
                    "intent": "CANCEL_ACTION",
                    "module": "orchestrator",
                    "assistant_text": reply,
                    "needs_confirmation": False
                }

        # Handle cancellation while in a slot-filling flow
        if intent == "CANCEL_ACTION":
            save_conversation_state(session_id, {})
            reply = "Action cancelled. What else can I help you with?"
            log_turn(session_id, account_id, effective_text, reply, "CANCEL_ACTION", "orchestrator")
            return {
                "session_id": session_id,
                "recognized_text": recognized_audio_text,
                "intent": "CANCEL_ACTION",
                "module": "orchestrator",
                "assistant_text": reply,
                "needs_confirmation": False
            }

        # 5. Slot collection for multi-turn flow
        awaiting_slot = conv_state.get("awaiting_slot")
        if awaiting_slot and conv_state.get("active_intent"):
            intent = conv_state["active_intent"]
            slots = conv_state.get("slots", {})
            if awaiting_slot == "date":
                slots["date"] = entities.get("date", effective_text)
            elif awaiting_slot == "reason":
                slots["reason"] = entities.get("reason", effective_text)
            elif awaiting_slot == "event_name":
                slots["event_name"] = entities.get("event_name", effective_text)
            elif awaiting_slot == "request_id":
                slots["request_id"] = entities.get("request_id", effective_text.upper())
            conv_state["slots"] = slots
            conv_state["awaiting_slot"] = None
        else:
            slots = conv_state.get("slots", {})
            slots.update(entities)
            conv_state["slots"] = slots

        # 6. Check Knowledge Agent for UNKNOWN or informational search
        if intent == "UNKNOWN":
            knowledge_res = self.knowledge_agent.handle({"user_text": effective_text})
            if knowledge_res.get("found"):
                final_text = self.response_agent.compose_response(knowledge_res, intent="SEARCH_KNOWLEDGE", context=conv_state)
                log_turn(session_id, account_id, effective_text, final_text, "SEARCH_KNOWLEDGE", "knowledge")
                return {
                    "session_id": session_id,
                    "recognized_text": recognized_audio_text,
                    "intent": "SEARCH_KNOWLEDGE",
                    "module": "knowledge",
                    "assistant_text": final_text,
                    "needs_confirmation": False
                }
            else:
                reply = "I didn't recognize that command. You can ask for attendance, timetable, exam dates, college info, or submit leave."
                log_turn(session_id, account_id, effective_text, reply, "UNKNOWN", "orchestrator")
                return {
                    "session_id": session_id,
                    "recognized_text": recognized_audio_text,
                    "intent": "UNKNOWN",
                    "module": "orchestrator",
                    "assistant_text": reply,
                    "needs_confirmation": False
                }

        # 7. Route to matching specialist agent
        context = {
            "session_id": session_id,
            "account_id": account_id,
            "role": role,
            "token": token,
            "intent": intent,
            "slots": slots,
            "user_text": effective_text
        }
        
        target_agent = None
        for agent in self.agents:
            if agent.can_handle(intent, role):
                target_agent = agent
                break
                
        if not target_agent:
            reply = f"Operation '{intent}' is not authorized for your current role ({role}). Please sign in with appropriate credentials."
            log_turn(session_id, account_id, effective_text, reply, intent, "security")
            return {
                "session_id": session_id,
                "recognized_text": recognized_audio_text,
                "intent": intent,
                "module": "security",
                "assistant_text": reply,
                "needs_confirmation": False
            }
            
        res = target_agent.handle(context)

        # 8. Use Response Agent for natural response formulation
        final_assistant_text = self.response_agent.compose_response(res, intent=intent, context=conv_state)
        
        # 9. Update multi-turn state
        if res.get("awaiting_slot"):
            conv_state["active_intent"] = intent
            conv_state["awaiting_slot"] = res["awaiting_slot"]
            conv_state["slots"] = res.get("updated_slots", slots)
            save_conversation_state(session_id, conv_state)
        elif not res.get("needs_confirmation"):
            save_conversation_state(session_id, {})
            
        log_turn(session_id, account_id, effective_text, final_assistant_text, intent, target_agent.name)
        
        return {
            "session_id": session_id,
            "recognized_text": recognized_audio_text,
            "intent": intent,
            "module": target_agent.name,
            "assistant_text": final_assistant_text,
            "pending_action": res.get("pending_action"),
            "needs_confirmation": res.get("needs_confirmation", False),
            "context": conv_state
        }

orchestrator = MasterOrchestrator()
