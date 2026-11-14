import json
import logging
from typing import Optional, Dict, Any
import httpx
from backend.llm.model_config import llm_config

logger = logging.getLogger(__name__)

class LocalLLMClient:
    def __init__(self, config=llm_config):
        self.config = config
        self._is_available: Optional[bool] = None

    def check_availability(self) -> bool:
        """Checks if local Ollama instance is reachable."""
        if not self.config.enabled:
            return False
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{self.config.base_url}/api/tags")
                self._is_available = (res.status_code == 200)
                return self._is_available
        except Exception:
            self._is_available = False
            return False

    def is_available(self) -> bool:
        if self._is_available is None:
            return self.check_availability()
        return self._is_available

    def generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        """Synchronous prompt generation with strict timeout."""
        if not self.is_available():
            return None
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature
            }
        }
        if system:
            payload["system"] = system

        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                res = client.post(f"{self.config.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
        except Exception as e:
            logger.warning("LLM request failed: %s", e)
            self._is_available = False
        return None

llm_client = LocalLLMClient()

