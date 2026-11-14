"""
Response Agent: Central natural-language response composition layer.
Receives verified specialist agent results and formulates clear, accurate, conversational responses
suitable for speech generation, with LLM enhancement and deterministic fallbacks.
"""
from typing import Dict, Any, Optional
from backend.llm.client import llm_client

RESPONSE_GENERATION_SYSTEM_PROMPT = """You are the response formatting assistant for Knotopian Institute of Technology (KIT).
Your job is to rephrase verified college data into a concise, polite, natural spoken response (1 to 2 sentences).
Strict guidelines:
- Never invent or fabricate data. Only use facts provided in the tool output.
- Keep responses clear and easy to understand when spoken aloud.
- If the operation failed, state the error clearly without making excuses.
- If input or confirmation is required, state the question directly.
"""

class ResponseAgent:
    name = "response_agent"

    def __init__(self, client=llm_client):
        self.client = client

    def compose_response(
        self,
        agent_result: Dict[str, Any],
        intent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        base_text = agent_result.get("assistant_text", "")
        status = agent_result.get("status", "success")

        # If LLM is available and this is an informational query, polish it concisely
        if self.client.is_available() and not agent_result.get("needs_confirmation"):
            try:
                data_summary = str(agent_result.get("data") or base_text)
                prompt = f"Intent: {intent}\nVerified Data: {data_summary}\nDefault wording: \"{base_text}\"\nPlease generate a friendly spoken response:"
                polished = self.client.generate(prompt, system=RESPONSE_GENERATION_SYSTEM_PROMPT)
                if polished and len(polished.strip()) > 10:
                    return polished.strip()
            except Exception:
                pass

        # Deterministic wording
        return base_text

response_agent = ResponseAgent()

