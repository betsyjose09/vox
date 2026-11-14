import logging
from typing import Dict, Any, List, Optional
from backend.llm.client import llm_client
from backend.llm.prompt_builder import SYSTEM_NLU_PROMPT, build_nlu_prompt
from backend.llm.output_validator import validate_llm_json, NLUInterpretation
from backend.llm.fallback import deterministic_fallback_interpret

logger = logging.getLogger(__name__)

class ConversationEngine:
    def __init__(self, client=llm_client):
        self.client = client

    def interpret_user_turn(
        self,
        user_text: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        active_context: Optional[Dict[str, Any]] = None
    ) -> NLUInterpretation:
        history = conversation_history or []
        context = active_context or {}

        # 1. Try local LLM if available
        if self.client.is_available():
            try:
                prompt = build_nlu_prompt(user_text, history, context)
                raw_resp = self.client.generate(prompt, system=SYSTEM_NLU_PROMPT)
                if raw_resp:
                    parsed = validate_llm_json(raw_resp)
                    if parsed:
                        return parsed
            except Exception as e:
                logger.warning("LLM turn interpretation failed: %s", e)

        # 2. Fall back to deterministic pipeline
        return deterministic_fallback_interpret(user_text, context)

conversation_engine = ConversationEngine()

