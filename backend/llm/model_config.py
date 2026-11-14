import os
from pydantic import BaseModel

class LLMConfig(BaseModel):
    enabled: bool = os.getenv("LLM_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    provider: str = os.getenv("LLM_PROVIDER", "ollama")  # 'ollama' or 'local'
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model: str = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    timeout_seconds: float = float(os.getenv("LLM_TIMEOUT", "2.5"))
    temperature: float = 0.1

llm_config = LLMConfig()

