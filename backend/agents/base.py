from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    name: str

    @abstractmethod
    def can_handle(self, intent: str, role: str) -> bool:
        pass

    @abstractmethod
    def handle(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
