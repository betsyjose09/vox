import math
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from backend.config import settings

def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer and lowercaser."""
    return re.findall(r"\b\w{2,}\b", text.lower())

class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.total_docs: int = 0
        
    def load_documents_from_dir(self, doc_dir: Path) -> int:
        self.chunks.clear()
        doc_dir = Path(doc_dir)
        if not doc_dir.exists():
            return 0
            
        for filepath in doc_dir.glob("*.txt"):
            content = filepath.read_text(encoding="utf-8")
            # Split by markdown headers or double newlines into coherent chunks
            sections = re.split(r"\n(?=##?\s)", content)
            for sec in sections:
                sec = sec.strip()
                if not sec:
                    continue
                lines = sec.split("\n", 1)
                header = lines[0].replace("#", "").strip() if lines else "General"
                tokens = tokenize(sec)
                if not tokens:
                    continue
                self.chunks.append({
                    "source": filepath.name,
                    "section": header,
                    "content": sec,
                    "tokens": tokens
                })
                
        self.total_docs = len(self.chunks)
        if self.total_docs == 0:
            return 0
            
        self.doc_lengths = [len(c["tokens"]) for c in self.chunks]
        self.avg_doc_len = sum(self.doc_lengths) / self.total_docs
        
        # Calculate document frequencies
        self.doc_freqs.clear()
        for c in self.chunks:
            unique_terms = set(c["tokens"])
            for t in unique_terms:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1
                
        return self.total_docs

    def search(self, query: str, top_k: int = 3, threshold: float = 1.0) -> List[Dict[str, Any]]:
        query_tokens = tokenize(query)
        if not query_tokens or self.total_docs == 0:
            return []
            
        scores = [0.0] * self.total_docs
        
        for q in query_tokens:
            df = self.doc_freqs.get(q, 0)
            if df == 0:
                continue
            # Standard Lucene/BM25 IDF
            idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
            
            for i, c in enumerate(self.chunks):
                tf = c["tokens"].count(q)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                scores[i] += idf * (numerator / denominator)
                
        ranked = sorted(
            [{"score": round(scores[i], 3), **self.chunks[i]} for i in range(self.total_docs) if scores[i] >= threshold],
            key=lambda x: x["score"],
            reverse=True
        )
        return ranked[:top_k]

bm25_retriever = BM25Retriever()
# Index documents at initialization
bm25_retriever.load_documents_from_dir(settings.documents_dir)

