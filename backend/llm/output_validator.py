import json
import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

VALID_INTENTS = {
    "GET_ATTENDANCE", "GET_TIMETABLE", "GET_MY_REQUESTS", "SUBMIT_LEAVE", "SUBMIT_ON_DUTY",
    "LIST_PENDING", "APPROVE_REQUEST", "REJECT_REQUEST", "CONFIRM_ACTION", "CANCEL_ACTION",
    "GET_COLLEGE_INFO", "GET_COURSES", "GET_ELIGIBILITY", "GET_HOLIDAYS", "GET_EXAM_DATES",
    "SEARCH_KNOWLEDGE", "GREETING", "UNKNOWN"
}

class NLUInterpretation(BaseModel):
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    confidence: float = 0.5

def validate_llm_json(raw_text: str) -> Optional[NLUInterpretation]:
    """Extracts, parses, and validates structured NLU output from LLM."""
    if not raw_text:
        return None
    # Strip potential markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
        intent = data.get("intent", "").upper().strip()
        if intent not in VALID_INTENTS:
            intent = "UNKNOWN"

        entities = data.get("entities", {})
        if not isinstance(entities, dict):
            entities = {}

        return NLUInterpretation(
            intent=intent,
            entities=entities,
            requires_clarification=bool(data.get("requires_clarification", False)),
            clarification_question=data.get("clarification_question"),
            confidence=float(data.get("confidence", 0.8))
        )
    except Exception:
        return None

