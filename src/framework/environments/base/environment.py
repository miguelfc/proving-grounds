from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import datetime

@dataclass
class Email:
    id: str
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

class Environment(ABC):
    """
    Abstract Base Class for a simulated environment.
    The environment maintains the state of the world (e.g., database, files).
    """
    
    @abstractmethod
    def reset(self):
        """Resets the environment to its initial state."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Returns the current state of the environment."""
        pass
