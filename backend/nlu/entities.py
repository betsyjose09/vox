import re
from typing import Dict, Any, Optional

def extract_entities(text: str) -> Dict[str, Any]:
    """
    Extracts structured slots from user input text (dates, request IDs, reasons).
    """
    entities: Dict[str, Any] = {}
    lower = text.lower()
    
    # 1. Date extraction
    if "today" in lower:
        entities["date"] = "today"
    elif "tomorrow" in lower:
        entities["date"] = "tomorrow"
    else:
        # Match YYYY-MM-DD
        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        if date_match:
            entities["date"] = date_match.group(1)
            
    # 2. Request ID extraction (e.g. REQ-9012 or 9012)
    req_match = re.search(r"\b(REQ-?\d{4,5})\b", text, re.IGNORECASE)
    if req_match:
        val = req_match.group(1).upper()
        if not val.startswith("REQ-"):
            val = val.replace("REQ", "REQ-")
        entities["request_id"] = val
    else:
        num_match = re.search(r"\b(request\s+#?(\d{4,5}))\b", text, re.IGNORECASE)
        if num_match:
            entities["request_id"] = f"REQ-{num_match.group(2)}"
            
    # 3. Leave reason extraction
    for reason in ["medical appointment", "sick leave", "family function", "fever", "personal reason", "emergency"]:
        if reason in lower:
            entities["reason"] = reason
            break
            
    # 4. On-Duty event extraction
    for event in ["hackathon", "symposium", "paper presentation", "sports meet", "conference"]:
        if event in lower:
            entities["event_name"] = event
            break
            
    return entities

