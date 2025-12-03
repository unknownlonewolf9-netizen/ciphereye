from abc import ABC, abstractmethod
from typing import Any, Dict

class OSINTModule(ABC):
    name: str = "base"
    description: str = "Base OSINT module"

    @abstractmethod
    def run(self, target: str, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError
