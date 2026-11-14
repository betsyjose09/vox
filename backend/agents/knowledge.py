from typing import Dict, Any
from backend.agents.base import BaseAgent
from backend.nlu.intents import Intent
from backend.knowledge.index import bm25_retriever

class KnowledgeAgent(BaseAgent):
    name = "knowledge"

    def can_handle(self, intent: str, role: str) -> bool:
        return intent == Intent.SEARCH_KNOWLEDGE.value

    def handle(self, ctx: Dict[str, Any]) -> Dict[str, Any]:
        query = ctx.get("user_text", "")
        results = bm25_retriever.search(query, top_k=2, threshold=1.0)
        
        if not results:
            return {
                "assistant_text": "I couldn't find official policy documents matching your question. Please consult the KIT Academic Dean's office.",
                "module": self.name,
                "found": False
            }
            
        top = results[0]
        snippet = top["content"][:300].strip().replace("\n", " ")
        citation = f"[Source: {top['source']} - {top['section']}]"
        
        return {
            "assistant_text": f"{snippet} {citation}",
            "module": self.name,
            "found": True,
            "citation": citation,
            "results": results
        }
