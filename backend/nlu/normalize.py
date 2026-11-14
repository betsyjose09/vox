import re

def normalize_text(text: str) -> str:
    """Normalizes input text by lowercasing, stripping punctuation, and trimming whitespace."""
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

