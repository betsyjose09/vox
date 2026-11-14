from typing import Dict, Any, Tuple
from backend.nlu.classifier import intent_classifier
from backend.nlu.entities import extract_entities
from backend.llm.output_validator import NLUInterpretation

def deterministic_fallback_interpret(user_text: str, active_context: Dict[str, Any]) -> NLUInterpretation:
    """Fast, deterministic fallback using TF-IDF + LogisticRegression + Regex entities."""
    intent, score, entities = intent_classifier.classify(user_text)
    
    # Handle contextual slot answers
    awaiting_slot = active_context.get("awaiting_slot")
    if awaiting_slot and intent == "UNKNOWN":
        # Slot continuation
        if awaiting_slot == "date":
            date_val = entities.get("date") or ("today" if "today" in user_text.lower() else "tomorrow" if "tomorrow" in user_text.lower() else user_text.strip())
            entities["date"] = date_val
        elif awaiting_slot == "reason":
            entities["reason"] = entities.get("reason") or user_text.strip()
        elif awaiting_slot == "event_name":
            entities["event_name"] = entities.get("event_name") or user_text.strip()
        elif awaiting_slot == "request_id":
            entities["request_id"] = entities.get("request_id") or user_text.strip().upper()
        intent = active_context.get("active_intent", "UNKNOWN")

    return NLUInterpretation(
        intent=intent,
        entities=entities,
        requires_clarification=False,
        clarification_question=None,
        confidence=float(score)
    )

